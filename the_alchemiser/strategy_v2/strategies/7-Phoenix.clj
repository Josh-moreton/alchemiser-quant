(defsymphony
 "Pheonix and Jörmungandr | Negative DD Correlation | No Sub Sorts | AR: 104% | DD: 7.4% | BT 06/21/19"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-inverse-volatility
  50
  [(group
    "Pheonix and Jörmungandr"
    [(weight-equal
      [(filter
        (cumulative-return {:window 6})
        (select-top 3)
        [(group
          "TUSI Custom/Energy Momentum V3 (Final)"
          [(weight-equal
            [(group
              "TUSI Custom"
              [(weight-equal
                [(group
                  "Vol Hedge Logic Group"
                  [(weight-equal
                    [(if
                      (> (rsi "QQQ" {:window 10}) 80)
                      [(weight-equal
                        [(asset
                          "UVXY"
                          "ProShares Ultra VIX Short-Term Futures ETF")
                         (asset
                          "BTAL"
                          "AGF U.S. Market Neutral Anti-Beta Fund")])]
                      [(group
                        "Vol Hedge Logic Group"
                        [(weight-specified
                          0.25
                          (group
                           "Spy max dd check | 2.4% cagr, 10.3% stdev, 20.6% dd, 0.29 sharpe, 0.12 calmar, -0.23 beta"
                           [(weight-equal
                             [(if
                               (> (max-drawdown "SPY" {:window 10}) 5)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])
                              (if
                               (> (max-drawdown "SPY" {:window 20}) 7)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])
                              (if
                               (> (max-drawdown "SPY" {:window 40}) 10)
                               [(weight-equal
                                 [(weight-equal
                                   [(asset
                                     "UVXY"
                                     "ProShares Ultra VIX Short-Term Futures ETF")
                                    (asset "GLD" "SPDR Gold Shares")
                                    (asset
                                     "UUP"
                                     "Invesco DB US Dollar Index Bullish Fund")
                                    (asset
                                     "IEF"
                                     "iShares 7-10 Year Treasury Bond ETF")
                                    (asset
                                     "BTAL"
                                     "AGF U.S. Market Neutral Anti-Beta Fund")])])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])])])
                          0.4
                          (group
                           "Vix RSI Check | 6.3% cagr, 9.6% stdev, 13.4% dd, 0.68 sharpe, 0.47 calmar, -0.08 beta"
                           [(weight-equal
                             [(if
                               (> (rsi "VIXY" {:window 20}) 65)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])
                              (if
                               (> (rsi "VIXY" {:window 40}) 60)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])
                              (if
                               (> (rsi "VIXY" {:window 60}) 60)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])])])
                          0.2
                          (group
                           "Spy stdev check | 0.7% cagr, 15.1% stdev, 35.9% dd, 0.12 sharpe, 0.02 calmar, -0.41 beta"
                           [(weight-specified
                             0.35
                             (if
                              (>
                               (stdev-return "SPY" {:window 21})
                               1.25)
                              [(weight-equal
                                [(asset
                                  "UVXY"
                                  "ProShares Ultra VIX Short-Term Futures ETF")
                                 (asset
                                  "BTAL"
                                  "AGF U.S. Market Neutral Anti-Beta Fund")
                                 (asset
                                  "IEF"
                                  "iShares 7-10 Year Treasury Bond ETF")
                                 (asset
                                  "UUP"
                                  "Invesco DB US Dollar Index Bullish Fund")])]
                              [(weight-equal
                                [(asset "GLD" "SPDR Gold Shares")
                                 (asset
                                  "UUP"
                                  "Invesco DB US Dollar Index Bullish Fund")
                                 (asset
                                  "XLP"
                                  "Consumer Staples Select Sector SPDR Fund")
                                 (asset
                                  "SHY"
                                  "iShares 1-3 Year Treasury Bond ETF")])])
                             0.65
                             (if
                              (> (stdev-return "SPY" {:window 21}) 1.5)
                              [(weight-equal
                                [(asset
                                  "UVXY"
                                  "ProShares Ultra VIX Short-Term Futures ETF")
                                 (asset
                                  "BTAL"
                                  "AGF U.S. Market Neutral Anti-Beta Fund")
                                 (asset
                                  "IEF"
                                  "iShares 7-10 Year Treasury Bond ETF")
                                 (asset
                                  "UUP"
                                  "Invesco DB US Dollar Index Bullish Fund")])]
                              [(weight-equal
                                [(asset "GLD" "SPDR Gold Shares")
                                 (asset
                                  "UUP"
                                  "Invesco DB US Dollar Index Bullish Fund")
                                 (asset
                                  "XLP"
                                  "Consumer Staples Select Sector SPDR Fund")
                                 (asset
                                  "SHY"
                                  "iShares 1-3 Year Treasury Bond ETF")])]))])
                          0.15
                          (group
                           "Vix stdev check | 0.3% cagr, 15% stdev, 39.5% dd, 0.09 sharpe, 0.01 calmar, -0.39 beta"
                           [(weight-equal
                             [(if
                               (> (stdev-return "VIXY" {:window 40}) 5)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])
                              (if
                               (> (stdev-return "VIXY" {:window 40}) 6)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])])]))])])])])])])
             (group
              "Energy Momentum V3 (Final)"
              [(weight-equal
                [(weight-equal
                  [(group
                    "Natural Gas"
                    [(weight-equal
                      [(weight-equal
                        [(if
                          (>
                           (moving-average-price "FCG" {:window 100})
                           (moving-average-price "FCG" {:window 500}))
                          [(weight-specified
                            0.9
                            (asset "FCG" "First Trust Natural Gas ETF")
                            0.1
                            (if
                             (>
                              (current-price "UNG")
                              (moving-average-price
                               "UNG"
                               {:window 50}))
                             [(asset
                               "BOIL"
                               "ProShares Ultra Bloomberg Natural Gas")]
                             [(asset
                               "KOLD"
                               "ProShares UltraShort Bloomberg Natural Gas")]))]
                          [(weight-equal
                            [(if
                              (<
                               (moving-average-price
                                "UNG"
                                {:window 50})
                               (moving-average-price
                                "UNG"
                                {:window 400}))
                              [(weight-equal
                                [(if
                                  (<
                                   (current-price "UNG")
                                   (moving-average-price
                                    "UNG"
                                    {:window 10}))
                                  [(weight-equal
                                    [(asset
                                      "KOLD"
                                      "ProShares UltraShort Bloomberg Natural Gas")
                                     (asset
                                      "SHY"
                                      "iShares 1-3 Year Treasury Bond ETF")])]
                                  [(weight-equal
                                    [(asset
                                      "SHV"
                                      "iShares Short Treasury Bond ETF")])])])]
                              [(weight-equal
                                [(asset
                                  "UNG"
                                  "United States Natural Gas Fund LP")])])])])])])])
                   (group
                    "Clean Energy"
                    [(weight-equal
                      [(if
                        (>
                         (current-price "ICLN")
                         (moving-average-price "ICLN" {:window 200}))
                        [(weight-equal
                          [(if
                            (>
                             (moving-average-price "ICLN" {:window 9})
                             (moving-average-price
                              "ICLN"
                              {:window 21}))
                            [(weight-equal
                              [(asset
                                "ICLN"
                                "iShares Global Clean Energy ETF")
                               (asset "TAN" "Invesco Solar ETF")
                               (asset
                                "FAN"
                                "First Trust Global Wind Energy ETF")])]
                            [(asset
                              "SHV"
                              "iShares Short Treasury Bond ETF")])])]
                        [(asset
                          "SHV"
                          "iShares Short Treasury Bond ETF")])])])
                   (group
                    "Oil"
                    [(weight-equal
                      [(group
                        "There Will Be Blood"
                        [(weight-equal
                          [(if
                            (>=
                             (exponential-moving-average-price
                              "DBO"
                              {:window 50})
                             (moving-average-price
                              "DBO"
                              {:window 200}))
                            [(weight-equal
                              [(if
                                (>
                                 (moving-average-price
                                  "NRGU"
                                  {:window 9})
                                 (moving-average-price
                                  "NRGU"
                                  {:window 21}))
                                [(weight-equal
                                  [(if
                                    (<
                                     (cumulative-return
                                      "NRGU"
                                      {:window 30})
                                     -10)
                                    [(weight-equal
                                      [(filter
                                        (moving-average-return
                                         {:window 21})
                                        (select-top 2)
                                        [(asset
                                          "XOM"
                                          "Exxon Mobil Corporation")
                                         (asset
                                          "XLE"
                                          "Energy Select Sector SPDR Fund")
                                         (asset
                                          "ENPH"
                                          "Enphase Energy, Inc.")
                                         (asset
                                          "VLO"
                                          "Valero Energy Corporation")
                                         (asset
                                          "CVE"
                                          "Cenovus Energy Inc.")
                                         (asset
                                          "CVX"
                                          "Chevron Corporation")
                                         (asset "COP" "ConocoPhillips")
                                         (asset
                                          "MPC"
                                          "Marathon Petroleum Corporation")
                                         (asset
                                          "DINO"
                                          "HF Sinclair Corporation")])])]
                                    [(weight-equal
                                      [(filter
                                        (rsi {:window 9})
                                        (select-top 1)
                                        [(asset
                                          "NRGU"
                                          "MicroSectors U.S. Big Oil Index 3X Leveraged ETN")
                                         (asset
                                          "OILK"
                                          "ProShares K-1 Free Crude Oil Strategy ETF")])])])
                                   (filter
                                    (moving-average-return
                                     {:window 21})
                                    (select-top 2)
                                    [(asset
                                      "XOM"
                                      "Exxon Mobil Corporation")
                                     (asset
                                      "XLE"
                                      "Energy Select Sector SPDR Fund")
                                     (asset
                                      "ENPH"
                                      "Enphase Energy, Inc.")
                                     (asset
                                      "VLO"
                                      "Valero Energy Corporation")
                                     (asset
                                      "CVE"
                                      "Cenovus Energy Inc.")
                                     (asset
                                      "CVX"
                                      "Chevron Corporation")
                                     (asset "COP" "ConocoPhillips")
                                     (asset
                                      "MPC"
                                      "Marathon Petroleum Corporation")
                                     (asset
                                      "DINO"
                                      "HF Sinclair Corporation")])])]
                                [(weight-equal
                                  [(filter
                                    (moving-average-return
                                     {:window 100})
                                    (select-top 2)
                                    [(asset
                                      "XOM"
                                      "Exxon Mobil Corporation")
                                     (asset
                                      "ENPH"
                                      "Enphase Energy, Inc.")
                                     (asset
                                      "VLO"
                                      "Valero Energy Corporation")
                                     (asset
                                      "CVE"
                                      "Cenovus Energy Inc.")
                                     (asset
                                      "CVX"
                                      "Chevron Corporation")
                                     (asset "COP" "ConocoPhillips")
                                     (asset
                                      "MPC"
                                      "Marathon Petroleum Corporation")
                                     (asset
                                      "DINO"
                                      "HF Sinclair Corporation")])])])])]
                            [(weight-equal
                              [(if
                                (<=
                                 (moving-average-price
                                  "OILK"
                                  {:window 50})
                                 (moving-average-price
                                  "OILK"
                                  {:window 400}))
                                [(weight-equal
                                  [(if
                                    (<
                                     (moving-average-return
                                      "NRGU"
                                      {:window 5})
                                     0)
                                    [(weight-equal
                                      [(filter
                                        (rsi {:window 7})
                                        (select-top 1)
                                        [(asset
                                          "NRGD"
                                          "MicroSectors U.S. Big Oil Index -3X Inverse Leveraged ETN")
                                         (asset
                                          "IEF"
                                          "iShares 7-10 Year Treasury Bond ETF")])])]
                                    [(weight-equal
                                      [(filter
                                        (rsi {:window 10})
                                        (select-top 1)
                                        [(asset
                                          "NRGU"
                                          "MicroSectors U.S. Big Oil Index 3X Leveraged ETN")
                                         (asset
                                          "OILK"
                                          "ProShares K-1 Free Crude Oil Strategy ETF")])])])
                                   (filter
                                    (moving-average-return
                                     {:window 100})
                                    (select-top 2)
                                    [(asset
                                      "XOM"
                                      "Exxon Mobil Corporation")
                                     (asset
                                      "ENPH"
                                      "Enphase Energy, Inc.")
                                     (asset
                                      "VLO"
                                      "Valero Energy Corporation")
                                     (asset
                                      "CVE"
                                      "Cenovus Energy Inc.")
                                     (asset
                                      "CVX"
                                      "Chevron Corporation")
                                     (asset "COP" "ConocoPhillips")
                                     (asset
                                      "MPC"
                                      "Marathon Petroleum Corporation")
                                     (asset
                                      "DINO"
                                      "HF Sinclair Corporation")])])]
                                [(weight-equal
                                  [(filter
                                    (moving-average-return
                                     {:window 100})
                                    (select-top 2)
                                    [(asset
                                      "XOM"
                                      "Exxon Mobil Corporation")
                                     (asset
                                      "ENPH"
                                      "Enphase Energy, Inc.")
                                     (asset
                                      "VLO"
                                      "Valero Energy Corporation")
                                     (asset
                                      "CVE"
                                      "Cenovus Energy Inc.")
                                     (asset
                                      "CVX"
                                      "Chevron Corporation")
                                     (asset "COP" "ConocoPhillips")
                                     (asset
                                      "MPC"
                                      "Marathon Petroleum Corporation")
                                     (asset
                                      "DINO"
                                      "HF Sinclair Corporation")])])])])])])])])])
                   (group
                    "V2 XLE Momentum"
                    [(weight-equal
                      [(if
                        (>
                         (exponential-moving-average-price
                          "XLE"
                          {:window 30})
                         (moving-average-price "XLE" {:window 200}))
                        [(weight-equal
                          [(asset
                            "XLE"
                            "Energy Select Sector SPDR Fund")])]
                        [(weight-equal
                          [(asset
                            "SHV"
                            "iShares Short Treasury Bond ETF")])])])])])])])])])
         (group
          "(TMF/TMV/Gold Momentum)/Energy Momentum V3 (Final)"
          [(weight-equal
            [(group
              "TMF/TMV/Gold Momentum"
              [(weight-equal
                [(group
                  "TMV Momentum"
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
                               (moving-average-price
                                "TMV"
                                {:window 135}))
                              [(weight-equal
                                [(if
                                  (> (rsi "TMV" {:window 10}) 71)
                                  [(asset
                                    "SHV"
                                    "iShares Short Treasury Bond ETF")]
                                  [(weight-equal
                                    [(if
                                      (> (rsi "TMV" {:window 60}) 59)
                                      [(asset
                                        "TLT"
                                        "iShares 20+ Year Treasury Bond ETF")]
                                      [(asset
                                        "TMV"
                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                              [(asset
                                "BND"
                                "Vanguard Total Bond Market ETF")])])]
                          [(asset
                            "BND"
                            "Vanguard Total Bond Market ETF")])])])])])
                 (group
                  "TMF Momentum"
                  [(weight-specified
                    1
                    (if
                     (< (rsi "TMF" {:window 10}) 32)
                     [(asset
                       "TMF"
                       "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                     [(weight-equal
                       [(if
                         (>
                          (moving-average-price "TLT" {:window 15})
                          (moving-average-price "TLT" {:window 50}))
                         [(weight-equal
                           [(if
                             (> (rsi "TMF" {:window 10}) 72)
                             [(asset
                               "SHV"
                               "iShares Short Treasury Bond ETF")]
                             [(weight-equal
                               [(if
                                 (> (rsi "TMF" {:window 60}) 57)
                                 [(asset
                                   "TBF"
                                   "Proshares Short 20+ Year Treasury")]
                                 [(asset
                                   "TMF"
                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])]
                         [(asset
                           "SHV"
                           "iShares Short Treasury Bond ETF")])])]))])
                 (group
                  "Gold Momentum"
                  [(weight-equal
                    [(if
                      (>
                       (moving-average-price "GLD" {:window 200})
                       (moving-average-price "GLD" {:window 350}))
                      [(weight-equal
                        [(if
                          (>
                           (moving-average-price "GLD" {:window 60})
                           (moving-average-price "GLD" {:window 150}))
                          [(asset "GLD" nil)]
                          [(asset "SHV" nil)])])]
                      [(asset "SHV" nil)])])])])])
             (group
              "Energy Momentum V3 (Final)"
              [(weight-equal
                [(weight-equal
                  [(group
                    "Natural Gas"
                    [(weight-equal
                      [(weight-equal
                        [(if
                          (>
                           (moving-average-price "FCG" {:window 100})
                           (moving-average-price "FCG" {:window 500}))
                          [(weight-specified
                            0.9
                            (asset "FCG" "First Trust Natural Gas ETF")
                            0.1
                            (if
                             (>
                              (current-price "UNG")
                              (moving-average-price
                               "UNG"
                               {:window 50}))
                             [(asset
                               "BOIL"
                               "ProShares Ultra Bloomberg Natural Gas")]
                             [(asset
                               "KOLD"
                               "ProShares UltraShort Bloomberg Natural Gas")]))]
                          [(weight-equal
                            [(if
                              (<
                               (moving-average-price
                                "UNG"
                                {:window 50})
                               (moving-average-price
                                "UNG"
                                {:window 400}))
                              [(weight-equal
                                [(if
                                  (<
                                   (current-price "UNG")
                                   (moving-average-price
                                    "UNG"
                                    {:window 10}))
                                  [(weight-equal
                                    [(asset
                                      "KOLD"
                                      "ProShares UltraShort Bloomberg Natural Gas")
                                     (asset
                                      "SHY"
                                      "iShares 1-3 Year Treasury Bond ETF")])]
                                  [(weight-equal
                                    [(asset
                                      "SHV"
                                      "iShares Short Treasury Bond ETF")])])])]
                              [(weight-equal
                                [(asset
                                  "UNG"
                                  "United States Natural Gas Fund LP")])])])])])])])
                   (group
                    "Clean Energy"
                    [(weight-equal
                      [(if
                        (>
                         (current-price "ICLN")
                         (moving-average-price "ICLN" {:window 200}))
                        [(weight-equal
                          [(if
                            (>
                             (moving-average-price "ICLN" {:window 9})
                             (moving-average-price
                              "ICLN"
                              {:window 21}))
                            [(weight-equal
                              [(asset
                                "ICLN"
                                "iShares Global Clean Energy ETF")
                               (asset "TAN" "Invesco Solar ETF")
                               (asset
                                "FAN"
                                "First Trust Global Wind Energy ETF")])]
                            [(asset
                              "SHV"
                              "iShares Short Treasury Bond ETF")])])]
                        [(asset
                          "SHV"
                          "iShares Short Treasury Bond ETF")])])])
                   (group
                    "Oil"
                    [(weight-equal
                      [(group
                        "There Will Be Blood"
                        [(weight-equal
                          [(if
                            (>=
                             (exponential-moving-average-price
                              "DBO"
                              {:window 50})
                             (moving-average-price
                              "DBO"
                              {:window 200}))
                            [(weight-equal
                              [(if
                                (>
                                 (moving-average-price
                                  "NRGU"
                                  {:window 9})
                                 (moving-average-price
                                  "NRGU"
                                  {:window 21}))
                                [(weight-equal
                                  [(if
                                    (<
                                     (cumulative-return
                                      "NRGU"
                                      {:window 30})
                                     -10)
                                    [(weight-equal
                                      [(filter
                                        (moving-average-return
                                         {:window 21})
                                        (select-top 2)
                                        [(asset
                                          "XOM"
                                          "Exxon Mobil Corporation")
                                         (asset
                                          "XLE"
                                          "Energy Select Sector SPDR Fund")
                                         (asset
                                          "ENPH"
                                          "Enphase Energy, Inc.")
                                         (asset
                                          "VLO"
                                          "Valero Energy Corporation")
                                         (asset
                                          "CVE"
                                          "Cenovus Energy Inc.")
                                         (asset
                                          "CVX"
                                          "Chevron Corporation")
                                         (asset "COP" "ConocoPhillips")
                                         (asset
                                          "MPC"
                                          "Marathon Petroleum Corporation")
                                         (asset
                                          "DINO"
                                          "HF Sinclair Corporation")])])]
                                    [(weight-equal
                                      [(filter
                                        (rsi {:window 9})
                                        (select-top 1)
                                        [(asset
                                          "NRGU"
                                          "MicroSectors U.S. Big Oil Index 3X Leveraged ETN")
                                         (asset
                                          "OILK"
                                          "ProShares K-1 Free Crude Oil Strategy ETF")])])])
                                   (filter
                                    (moving-average-return
                                     {:window 21})
                                    (select-top 2)
                                    [(asset
                                      "XOM"
                                      "Exxon Mobil Corporation")
                                     (asset
                                      "XLE"
                                      "Energy Select Sector SPDR Fund")
                                     (asset
                                      "ENPH"
                                      "Enphase Energy, Inc.")
                                     (asset
                                      "VLO"
                                      "Valero Energy Corporation")
                                     (asset
                                      "CVE"
                                      "Cenovus Energy Inc.")
                                     (asset
                                      "CVX"
                                      "Chevron Corporation")
                                     (asset "COP" "ConocoPhillips")
                                     (asset
                                      "MPC"
                                      "Marathon Petroleum Corporation")
                                     (asset
                                      "DINO"
                                      "HF Sinclair Corporation")])])]
                                [(weight-equal
                                  [(filter
                                    (moving-average-return
                                     {:window 100})
                                    (select-top 2)
                                    [(asset
                                      "XOM"
                                      "Exxon Mobil Corporation")
                                     (asset
                                      "ENPH"
                                      "Enphase Energy, Inc.")
                                     (asset
                                      "VLO"
                                      "Valero Energy Corporation")
                                     (asset
                                      "CVE"
                                      "Cenovus Energy Inc.")
                                     (asset
                                      "CVX"
                                      "Chevron Corporation")
                                     (asset "COP" "ConocoPhillips")
                                     (asset
                                      "MPC"
                                      "Marathon Petroleum Corporation")
                                     (asset
                                      "DINO"
                                      "HF Sinclair Corporation")])])])])]
                            [(weight-equal
                              [(if
                                (<=
                                 (moving-average-price
                                  "OILK"
                                  {:window 50})
                                 (moving-average-price
                                  "OILK"
                                  {:window 400}))
                                [(weight-equal
                                  [(if
                                    (<
                                     (moving-average-return
                                      "NRGU"
                                      {:window 5})
                                     0)
                                    [(weight-equal
                                      [(filter
                                        (rsi {:window 7})
                                        (select-top 1)
                                        [(asset
                                          "NRGD"
                                          "MicroSectors U.S. Big Oil Index -3X Inverse Leveraged ETN")
                                         (asset
                                          "IEF"
                                          "iShares 7-10 Year Treasury Bond ETF")])])]
                                    [(weight-equal
                                      [(filter
                                        (rsi {:window 10})
                                        (select-top 1)
                                        [(asset
                                          "NRGU"
                                          "MicroSectors U.S. Big Oil Index 3X Leveraged ETN")
                                         (asset
                                          "OILK"
                                          "ProShares K-1 Free Crude Oil Strategy ETF")])])])
                                   (filter
                                    (moving-average-return
                                     {:window 100})
                                    (select-top 2)
                                    [(asset
                                      "XOM"
                                      "Exxon Mobil Corporation")
                                     (asset
                                      "ENPH"
                                      "Enphase Energy, Inc.")
                                     (asset
                                      "VLO"
                                      "Valero Energy Corporation")
                                     (asset
                                      "CVE"
                                      "Cenovus Energy Inc.")
                                     (asset
                                      "CVX"
                                      "Chevron Corporation")
                                     (asset "COP" "ConocoPhillips")
                                     (asset
                                      "MPC"
                                      "Marathon Petroleum Corporation")
                                     (asset
                                      "DINO"
                                      "HF Sinclair Corporation")])])]
                                [(weight-equal
                                  [(filter
                                    (moving-average-return
                                     {:window 100})
                                    (select-top 2)
                                    [(asset
                                      "XOM"
                                      "Exxon Mobil Corporation")
                                     (asset
                                      "ENPH"
                                      "Enphase Energy, Inc.")
                                     (asset
                                      "VLO"
                                      "Valero Energy Corporation")
                                     (asset
                                      "CVE"
                                      "Cenovus Energy Inc.")
                                     (asset
                                      "CVX"
                                      "Chevron Corporation")
                                     (asset "COP" "ConocoPhillips")
                                     (asset
                                      "MPC"
                                      "Marathon Petroleum Corporation")
                                     (asset
                                      "DINO"
                                      "HF Sinclair Corporation")])])])])])])])])])
                   (group
                    "V2 XLE Momentum"
                    [(weight-equal
                      [(if
                        (>
                         (exponential-moving-average-price
                          "XLE"
                          {:window 30})
                         (moving-average-price "XLE" {:window 200}))
                        [(weight-equal
                          [(asset
                            "XLE"
                            "Energy Select Sector SPDR Fund")])]
                        [(weight-equal
                          [(asset
                            "SHV"
                            "iShares Short Treasury Bond ETF")])])])])])])])])])
         (group
          "Commodities Macro Momentum/Block/BTC V2"
          [(weight-equal
            [(group
              "Commo Macro Momentum/Block"
              [(weight-equal
                [(group
                  "Commodities Macro Momentum"
                  [(weight-equal
                    [(if
                      (< (rsi "DBC" {:window 10}) 17)
                      [(asset
                        "DBC"
                        "Invesco DB Commodity Index Tracking Fund")]
                      [(weight-equal
                        [(if
                          (>
                           (moving-average-price "DBC" {:window 100})
                           (moving-average-price "DBC" {:window 252}))
                          [(weight-equal
                            [(if
                              (>
                               (moving-average-price
                                "DBC"
                                {:window 50})
                               (moving-average-price
                                "DBC"
                                {:window 100}))
                              [(weight-equal
                                [(if
                                  (> (rsi "DBC" {:window 60}) 60)
                                  [(asset
                                    "SHV"
                                    "iShares Short Treasury Bond ETF")]
                                  [(asset
                                    "DBC"
                                    "Invesco DB Commodity Index Tracking Fund")])])]
                              [(asset
                                "SHV"
                                "iShares Short Treasury Bond ETF")])])]
                          [(asset
                            "SHV"
                            "iShares Short Treasury Bond ETF")])])])])])
                 (group
                  "Commodity Block"
                  [(weight-specified
                    0.35
                    (group
                     "Commodities"
                     [(weight-equal
                       [(if
                         (< (rsi "DBC" {:window 10}) 15)
                         [(group
                           "Commodity Bundle"
                           [(weight-equal
                             [(asset "DBC" nil) (asset "XME" nil)])])]
                         [(group
                           "Short-Term Momentum"
                           [(weight-equal
                             [(if
                               (>
                                (exponential-moving-average-price
                                 "DBC"
                                 {:window 8})
                                (moving-average-price
                                 "DBC"
                                 {:window 70}))
                               [(group
                                 "Commodity Bundle"
                                 [(weight-equal
                                   [(asset "DBC" nil)
                                    (asset "XME" nil)])])]
                               [(asset "BIL" nil)])])])
                          (group
                           "Long-Term Momentum"
                           [(weight-equal
                             [(if
                               (>
                                (moving-average-price
                                 "DBC"
                                 {:window 100})
                                (moving-average-price
                                 "DBC"
                                 {:window 252}))
                               [(weight-equal
                                 [(if
                                   (>
                                    (moving-average-price
                                     "DBC"
                                     {:window 50})
                                    (moving-average-price
                                     "DBC"
                                     {:window 100}))
                                   [(weight-equal
                                     [(if
                                       (< (rsi "DBC" {:window 60}) 60)
                                       [(group
                                         "Commodity Bundle"
                                         [(weight-equal
                                           [(asset "DBC" nil)
                                            (asset "XME" nil)])])]
                                       [(asset "BIL" nil)])])]
                                   [(asset "BIL" nil)])])]
                               [(asset "BIL" nil)])])])])])])
                    0.25
                    (group
                     "Natural Gas"
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
                              (moving-average-price
                               "FCG"
                               {:window 400}))
                             [(asset "FCG" nil)]
                             [(group
                               "Long/Short"
                               [(weight-equal
                                 [(if
                                   (>
                                    (current-price "FCG")
                                    (moving-average-price
                                     "FCG"
                                     {:window 10}))
                                   [(asset "FCG" nil)]
                                   [(group
                                     "KOLD Wrapper"
                                     [(weight-equal
                                       [(if
                                         (<
                                          (rsi "UNG" {:window 10})
                                          25)
                                         [(asset "BIL" nil)]
                                         [(asset
                                           "KOLD"
                                           nil)])])])])])])
                              (asset "BIL" nil)])])])])])
                    0.2
                    (group
                     "Gold"
                     [(weight-equal
                       [(if
                         (>
                          (moving-average-price "GLD" {:window 200})
                          (moving-average-price "GLD" {:window 350}))
                         [(weight-equal
                           [(if
                             (>
                              (moving-average-price "GLD" {:window 60})
                              (moving-average-price
                               "GLD"
                               {:window 150}))
                             [(asset "GLD" nil)]
                             [(asset "BIL" nil)])])]
                         [(asset "BIL" nil)])])])
                    0.2
                    (group
                     "Oil"
                     [(weight-equal
                       [(if
                         (< (rsi "UCO" {:window 10}) 15)
                         [(asset "DBO" nil)]
                         [(weight-equal
                           [(if
                             (>
                              (current-price "DBO")
                              (moving-average-price
                               "DBO"
                               {:window 130}))
                             [(weight-equal
                               [(if
                                 (>
                                  (exponential-moving-average-price
                                   "DBO"
                                   {:window 8})
                                  (moving-average-price
                                   "DBO"
                                   {:window 70}))
                                 [(asset "DBO" nil)]
                                 [(asset "BIL" nil)])])]
                             [(asset "BIL" nil)])])])])]))])])])
             (group
              "BTC V2"
              [(weight-equal
                [(if
                  (< (rsi "TQQQ" {:window 10}) 31)
                  [(asset
                    "TECL"
                    "Direxion Daily Technology Bull 3x Shares")]
                  [(weight-equal
                    [(if
                      (> (rsi "QQQ" {:window 10}) 80)
                      [(asset
                        "UVXY"
                        "ProShares Ultra VIX Short-Term Futures ETF")]
                      [(weight-equal
                        [(if
                          (> (rsi "SPY" {:window 10}) 80)
                          [(asset
                            "UVXY"
                            "ProShares Ultra VIX Short-Term Futures ETF")]
                          [(weight-equal
                            [(if
                              (>
                               (rsi "IEF" {:window 20})
                               (rsi "PSQ" {:window 20}))
                              [(weight-equal
                                [(if
                                  (>
                                   (exponential-moving-average-price
                                    "GBTC"
                                    {:window 9})
                                   (moving-average-price
                                    "GBTC"
                                    {:window 24}))
                                  [(asset
                                    "GBTC"
                                    "Grayscale Bitcoin Trust")]
                                  [(weight-equal
                                    [(asset
                                      "SHV"
                                      "iShares Short Treasury Bond ETF")])])])]
                              [(weight-equal
                                [(asset
                                  "SHV"
                                  "iShares Short Treasury Bond ETF")])])])])])])])])])])])])
         (group
          "TUSI Custom/ Cautious Fund Surfing"
          [(weight-equal
            [(group
              "TUSI Custom"
              [(weight-equal
                [(group
                  "Vol Hedge Logic Group"
                  [(weight-equal
                    [(if
                      (> (rsi "QQQ" {:window 10}) 80)
                      [(weight-equal
                        [(asset
                          "UVXY"
                          "ProShares Ultra VIX Short-Term Futures ETF")
                         (asset
                          "BTAL"
                          "AGF U.S. Market Neutral Anti-Beta Fund")])]
                      [(group
                        "Vol Hedge Logic Group"
                        [(weight-specified
                          0.25
                          (group
                           "Spy max dd check | 2.4% cagr, 10.3% stdev, 20.6% dd, 0.29 sharpe, 0.12 calmar, -0.23 beta"
                           [(weight-equal
                             [(if
                               (> (max-drawdown "SPY" {:window 10}) 5)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])
                              (if
                               (> (max-drawdown "SPY" {:window 20}) 7)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])
                              (if
                               (> (max-drawdown "SPY" {:window 40}) 10)
                               [(weight-equal
                                 [(weight-equal
                                   [(asset
                                     "UVXY"
                                     "ProShares Ultra VIX Short-Term Futures ETF")
                                    (asset "GLD" "SPDR Gold Shares")
                                    (asset
                                     "UUP"
                                     "Invesco DB US Dollar Index Bullish Fund")
                                    (asset
                                     "IEF"
                                     "iShares 7-10 Year Treasury Bond ETF")
                                    (asset
                                     "BTAL"
                                     "AGF U.S. Market Neutral Anti-Beta Fund")])])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])])])
                          0.4
                          (group
                           "Vix RSI Check | 6.3% cagr, 9.6% stdev, 13.4% dd, 0.68 sharpe, 0.47 calmar, -0.08 beta"
                           [(weight-equal
                             [(if
                               (> (rsi "VIXY" {:window 20}) 65)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])
                              (if
                               (> (rsi "VIXY" {:window 40}) 60)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])
                              (if
                               (> (rsi "VIXY" {:window 60}) 60)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])])])
                          0.2
                          (group
                           "Spy stdev check | 0.7% cagr, 15.1% stdev, 35.9% dd, 0.12 sharpe, 0.02 calmar, -0.41 beta"
                           [(weight-specified
                             0.35
                             (if
                              (>
                               (stdev-return "SPY" {:window 21})
                               1.25)
                              [(weight-equal
                                [(asset
                                  "UVXY"
                                  "ProShares Ultra VIX Short-Term Futures ETF")
                                 (asset
                                  "BTAL"
                                  "AGF U.S. Market Neutral Anti-Beta Fund")
                                 (asset
                                  "IEF"
                                  "iShares 7-10 Year Treasury Bond ETF")
                                 (asset
                                  "UUP"
                                  "Invesco DB US Dollar Index Bullish Fund")])]
                              [(weight-equal
                                [(asset "GLD" "SPDR Gold Shares")
                                 (asset
                                  "UUP"
                                  "Invesco DB US Dollar Index Bullish Fund")
                                 (asset
                                  "XLP"
                                  "Consumer Staples Select Sector SPDR Fund")
                                 (asset
                                  "SHY"
                                  "iShares 1-3 Year Treasury Bond ETF")])])
                             0.65
                             (if
                              (> (stdev-return "SPY" {:window 21}) 1.5)
                              [(weight-equal
                                [(asset
                                  "UVXY"
                                  "ProShares Ultra VIX Short-Term Futures ETF")
                                 (asset
                                  "BTAL"
                                  "AGF U.S. Market Neutral Anti-Beta Fund")
                                 (asset
                                  "IEF"
                                  "iShares 7-10 Year Treasury Bond ETF")
                                 (asset
                                  "UUP"
                                  "Invesco DB US Dollar Index Bullish Fund")])]
                              [(weight-equal
                                [(asset "GLD" "SPDR Gold Shares")
                                 (asset
                                  "UUP"
                                  "Invesco DB US Dollar Index Bullish Fund")
                                 (asset
                                  "XLP"
                                  "Consumer Staples Select Sector SPDR Fund")
                                 (asset
                                  "SHY"
                                  "iShares 1-3 Year Treasury Bond ETF")])]))])
                          0.15
                          (group
                           "Vix stdev check | 0.3% cagr, 15% stdev, 39.5% dd, 0.09 sharpe, 0.01 calmar, -0.39 beta"
                           [(weight-equal
                             [(if
                               (> (stdev-return "VIXY" {:window 40}) 5)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])
                              (if
                               (> (stdev-return "VIXY" {:window 40}) 6)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])])]))])])])])])])
             (group
              "V2 | Cautious Fund Surfing | 3x with V1.1 | Bear BUYDIPS, Bull HFEAR"
              [(weight-equal
                [(group
                  "1% stdev https://discord.gg/8e7bHnJMwE"
                  [(weight-equal
                    [(weight-equal
                      [(group
                        "14d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 14}) 1)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 14})
                                 (rsi "SHY" {:window 14}))
                                [(weight-inverse-volatility
                                  14
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                       (group
                        "21d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 21}) 1)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 21})
                                 (rsi "SHY" {:window 21}))
                                [(weight-inverse-volatility
                                  21
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                       (group
                        "28d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 28}) 1)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 28})
                                 (rsi "SHY" {:window 28}))
                                [(weight-inverse-volatility
                                  28
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                       (group
                        "35d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 35}) 1)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 35})
                                 (rsi "SHY" {:window 35}))
                                [(weight-inverse-volatility
                                  35
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                       (group
                        "42d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 42}) 1)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 42})
                                 (rsi "SHY" {:window 42}))
                                [(weight-inverse-volatility
                                  42
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])])])
                 (group
                  "1.5% stdev https://discord.gg/8e7bHnJMwE"
                  [(weight-equal
                    [(weight-equal
                      [(group
                        "14d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 14}) 1.5)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 14})
                                 (rsi "SHY" {:window 14}))
                                [(weight-inverse-volatility
                                  14
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                       (group
                        "21d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 21}) 1.5)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 21})
                                 (rsi "SHY" {:window 21}))
                                [(weight-inverse-volatility
                                  21
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                       (group
                        "28d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 28}) 1.5)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 28})
                                 (rsi "SHY" {:window 28}))
                                [(weight-inverse-volatility
                                  28
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                       (group
                        "35d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 35}) 1.5)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 35})
                                 (rsi "SHY" {:window 35}))
                                [(weight-inverse-volatility
                                  35
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                       (group
                        "42d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 42}) 1.5)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 42})
                                 (rsi "SHY" {:window 42}))
                                [(weight-inverse-volatility
                                  42
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])])])
                 (group
                  "2% stdev https://discord.gg/8e7bHnJMwE"
                  [(weight-equal
                    [(weight-equal
                      [(group
                        "14d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 14}) 2)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 14})
                                 (rsi "SHY" {:window 14}))
                                [(weight-inverse-volatility
                                  14
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                       (group
                        "21d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 21}) 2)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 21})
                                 (rsi "SHY" {:window 21}))
                                [(weight-inverse-volatility
                                  21
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                       (group
                        "35d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 35}) 2)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 35})
                                 (rsi "SHY" {:window 35}))
                                [(weight-inverse-volatility
                                  35
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                       (group
                        "28d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 28}) 2)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 28})
                                 (rsi "SHY" {:window 28}))
                                [(weight-inverse-volatility
                                  28
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                       (group
                        "42d"
                        [(weight-equal
                          [(if
                            (< (stdev-return "SPY" {:window 42}) 2)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "SPY" {:window 42})
                                 (rsi "SHY" {:window 42}))
                                [(weight-inverse-volatility
                                  42
                                  [(asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")])]
                                [(group
                                  "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown
                                        "SPY"
                                        {:window 252})
                                       10)
                                      [(group
                                        "Buy the Dips: Nasdaq 100/S&P 500"
                                        [(weight-equal
                                          [(group
                                            "Nasdaq Dip Check"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (cumulative-return
                                                  "QQQ"
                                                  {:window 5})
                                                 -5)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 1})
                                                     5)
                                                    [(weight-equal
                                                      [(group
                                                        "S&P500 Dip Check"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               5})
                                                             -5)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   1})
                                                                 5)
                                                                [(group
                                                                  "Safety Mix | UUP, GLD, & XLP"
                                                                  [(weight-equal
                                                                    [(asset
                                                                      "UUP"
                                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                                     (asset
                                                                      "GLD"
                                                                      "SPDR Gold Shares")
                                                                     (asset
                                                                      "XLP"
                                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                                [(asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])])]
                                                [(weight-equal
                                                  [(group
                                                    "S&P500 Dip Check"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 5})
                                                         -5)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               1})
                                                             5)
                                                            [(group
                                                              "Safety Mix | UUP, GLD, & XLP"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "GLD"
                                                                  "SPDR Gold Shares")
                                                                 (asset
                                                                  "XLP"
                                                                  "Consumer Staples Select Sector SPDR Fund")])])]
                                                            [(asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(group
                                                          "Safety Mix | UUP, GLD, & XLP"
                                                          [(weight-equal
                                                            [(asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "GLD"
                                                              "SPDR Gold Shares")
                                                             (asset
                                                              "XLP"
                                                              "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                      [(weight-equal
                                        [(group
                                          "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (max-drawdown
                                                "SPY"
                                                {:window 10})
                                               5)
                                              [(group
                                                "Risk ON"
                                                [(weight-specified
                                                  0.55
                                                  (weight-inverse-volatility
                                                   21
                                                   [(asset
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])
                                                  0.45
                                                  (asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                              [(group
                                                "Risk OFF"
                                                [(weight-equal
                                                  [(group
                                                    "Safety Mix | UUP, GLD, & XLP"
                                                    [(weight-equal
                                                      [(asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "XLP"
                                                        "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                            [(weight-equal
                              [(group
                                "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                [(weight-equal
                                  [(if
                                    (>
                                     (max-drawdown "SPY" {:window 252})
                                     10)
                                    [(group
                                      "Buy the Dips: Nasdaq 100/S&P 500"
                                      [(weight-equal
                                        [(group
                                          "Nasdaq Dip Check"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 5})
                                               -5)
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "TQQQ"
                                                    {:window 1})
                                                   5)
                                                  [(weight-equal
                                                    [(group
                                                      "S&P500 Dip Check"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (cumulative-return
                                                            "SPY"
                                                            {:window
                                                             5})
                                                           -5)
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (cumulative-return
                                                                "UPRO"
                                                                {:window
                                                                 1})
                                                               5)
                                                              [(group
                                                                "Safety Mix | UUP, GLD, & XLP"
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UUP"
                                                                    "Invesco DB US Dollar Index Bullish Fund")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "XLP"
                                                                    "Consumer Staples Select Sector SPDR Fund")])])]
                                                              [(asset
                                                                "UPRO"
                                                                "ProShares UltraPro S&P500")])])]
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])]
                                              [(weight-equal
                                                [(group
                                                  "S&P500 Dip Check"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "SPY"
                                                        {:window 5})
                                                       -5)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (cumulative-return
                                                            "UPRO"
                                                            {:window
                                                             1})
                                                           5)
                                                          [(group
                                                            "Safety Mix | UUP, GLD, & XLP"
                                                            [(weight-equal
                                                              [(asset
                                                                "UUP"
                                                                "Invesco DB US Dollar Index Bullish Fund")
                                                               (asset
                                                                "GLD"
                                                                "SPDR Gold Shares")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])]
                                                          [(asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(group
                                                        "Safety Mix | UUP, GLD, & XLP"
                                                        [(weight-equal
                                                          [(asset
                                                            "UUP"
                                                            "Invesco DB US Dollar Index Bullish Fund")
                                                           (asset
                                                            "GLD"
                                                            "SPDR Gold Shares")
                                                           (asset
                                                            "XLP"
                                                            "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (max-drawdown
                                              "SPY"
                                              {:window 10})
                                             5)
                                            [(group
                                              "Risk ON"
                                              [(weight-specified
                                                0.55
                                                (weight-inverse-volatility
                                                 21
                                                 [(asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")])
                                                0.45
                                                (asset
                                                 "TMF"
                                                 "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                            [(group
                                              "Risk OFF"
                                              [(weight-equal
                                                [(group
                                                  "Safety Mix | UUP, GLD, & XLP"
                                                  [(weight-equal
                                                    [(asset
                                                      "UUP"
                                                      "Invesco DB US Dollar Index Bullish Fund")
                                                     (asset
                                                      "GLD"
                                                      "SPDR Gold Shares")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])])])])])])])
         (group
          "(TMF/TMV/Gold Momentum)/Rising Rates Vol Switch Simple"
          [(weight-equal
            [(group
              "TMF/TMV/Gold Momentum"
              [(weight-equal
                [(group
                  "TMV Momentum"
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
                               (moving-average-price
                                "TMV"
                                {:window 135}))
                              [(weight-equal
                                [(if
                                  (> (rsi "TMV" {:window 10}) 71)
                                  [(asset
                                    "SHV"
                                    "iShares Short Treasury Bond ETF")]
                                  [(weight-equal
                                    [(if
                                      (> (rsi "TMV" {:window 60}) 59)
                                      [(asset
                                        "TLT"
                                        "iShares 20+ Year Treasury Bond ETF")]
                                      [(asset
                                        "TMV"
                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                              [(asset
                                "BND"
                                "Vanguard Total Bond Market ETF")])])]
                          [(asset
                            "BND"
                            "Vanguard Total Bond Market ETF")])])])])])
                 (group
                  "TMF Momentum"
                  [(weight-specified
                    1
                    (if
                     (< (rsi "TMF" {:window 10}) 32)
                     [(asset
                       "TMF"
                       "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                     [(weight-equal
                       [(if
                         (>
                          (moving-average-price "TLT" {:window 15})
                          (moving-average-price "TLT" {:window 50}))
                         [(weight-equal
                           [(if
                             (> (rsi "TMF" {:window 10}) 72)
                             [(asset
                               "SHV"
                               "iShares Short Treasury Bond ETF")]
                             [(weight-equal
                               [(if
                                 (> (rsi "TMF" {:window 60}) 57)
                                 [(asset
                                   "TBF"
                                   "Proshares Short 20+ Year Treasury")]
                                 [(asset
                                   "TMF"
                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])]
                         [(asset
                           "SHV"
                           "iShares Short Treasury Bond ETF")])])]))])
                 (group
                  "Gold Momentum"
                  [(weight-equal
                    [(if
                      (>
                       (moving-average-price "GLD" {:window 200})
                       (moving-average-price "GLD" {:window 350}))
                      [(weight-equal
                        [(if
                          (>
                           (moving-average-price "GLD" {:window 60})
                           (moving-average-price "GLD" {:window 150}))
                          [(asset "GLD" nil)]
                          [(asset "SHV" nil)])])]
                      [(asset "SHV" nil)])])])])])
             (group
              "Rising Rates Vol Switch Simple"
              [(weight-equal
                [(if
                  (> (rsi "QQQ" {:window 10}) 79)
                  [(weight-equal
                    [(asset
                      "UVXY"
                      "ProShares Ultra VIX Short-Term Futures ETF")])]
                  [(weight-equal
                    [(if
                      (< (rsi "QQQ" {:window 10}) 32)
                      [(weight-equal
                        [(filter
                          (rsi {:window 10})
                          (select-bottom 1)
                          [(asset "TQQQ" "ProShares UltraPro QQQ")
                           (asset
                            "BSV"
                            "Vanguard Short-Term Bond ETF")])])]
                      [(weight-equal
                        [(if
                          (> (max-drawdown "QQQ" {:window 12}) 6)
                          [(group
                            "Risk Off"
                            [(weight-equal
                              [(filter
                                (moving-average-return {:window 25})
                                (select-bottom 1)
                                [(asset
                                  "DBMF"
                                  "iMGP DBi Managed Futures Strategy ETF")
                                 (asset
                                  "SQQQ"
                                  "ProShares UltraPro Short QQQ")])])])]
                          [(weight-equal
                            [(if
                              (> (max-drawdown "TMF" {:window 10}) 7)
                              [(weight-equal
                                [(filter
                                  (rsi {:window 20})
                                  (select-bottom 1)
                                  [(asset
                                    "DBMF"
                                    "iMGP DBi Managed Futures Strategy ETF")
                                   (asset
                                    "TMV"
                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])]
                              [(weight-inverse-volatility
                                45
                                [(asset
                                  "TMF"
                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                 (asset
                                  "FAS"
                                  "Direxion Daily Financial Bull 3x Shares")
                                 (asset
                                  "TQQQ"
                                  "ProShares UltraPro QQQ")
                                 (asset
                                  "CURE"
                                  "Direxion Daily Healthcare Bull 3x Shares")
                                 (asset
                                  "SOXL"
                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                 (asset
                                  "UPRO"
                                  "ProShares UltraPro S&P500")
                                 (asset
                                  "LABU"
                                  "Direxion Daily S&P Biotech Bull 3X Shares")])])])])])])])])])])])])
         (group
          "Commo Macro/(TMF/TMV/Gold Momentum)"
          [(weight-equal
            [(group
              "TMF/TMV/Gold Momentum"
              [(weight-equal
                [(group
                  "TMV Momentum"
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
                               (moving-average-price
                                "TMV"
                                {:window 135}))
                              [(weight-equal
                                [(if
                                  (> (rsi "TMV" {:window 10}) 71)
                                  [(asset
                                    "SHV"
                                    "iShares Short Treasury Bond ETF")]
                                  [(weight-equal
                                    [(if
                                      (> (rsi "TMV" {:window 60}) 59)
                                      [(asset
                                        "TLT"
                                        "iShares 20+ Year Treasury Bond ETF")]
                                      [(asset
                                        "TMV"
                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                              [(asset
                                "BND"
                                "Vanguard Total Bond Market ETF")])])]
                          [(asset
                            "BND"
                            "Vanguard Total Bond Market ETF")])])])])])
                 (group
                  "TMF Momentum"
                  [(weight-specified
                    1
                    (if
                     (< (rsi "TMF" {:window 10}) 32)
                     [(asset
                       "TMF"
                       "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                     [(weight-equal
                       [(if
                         (>
                          (moving-average-price "TLT" {:window 15})
                          (moving-average-price "TLT" {:window 50}))
                         [(weight-equal
                           [(if
                             (> (rsi "TMF" {:window 10}) 72)
                             [(asset
                               "SHV"
                               "iShares Short Treasury Bond ETF")]
                             [(weight-equal
                               [(if
                                 (> (rsi "TMF" {:window 60}) 57)
                                 [(asset
                                   "TBF"
                                   "Proshares Short 20+ Year Treasury")]
                                 [(asset
                                   "TMF"
                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])]
                         [(asset
                           "SHV"
                           "iShares Short Treasury Bond ETF")])])]))])
                 (group
                  "Gold Momentum"
                  [(weight-equal
                    [(if
                      (>
                       (moving-average-price "GLD" {:window 200})
                       (moving-average-price "GLD" {:window 350}))
                      [(weight-equal
                        [(if
                          (>
                           (moving-average-price "GLD" {:window 60})
                           (moving-average-price "GLD" {:window 150}))
                          [(asset "GLD" nil)]
                          [(asset "SHV" nil)])])]
                      [(asset "SHV" nil)])])])])])
             (group
              "Commodities Macro Momentum"
              [(weight-equal
                [(if
                  (< (rsi "DBC" {:window 10}) 17)
                  [(asset
                    "DBC"
                    "Invesco DB Commodity Index Tracking Fund")]
                  [(weight-equal
                    [(if
                      (>
                       (moving-average-price "DBC" {:window 100})
                       (moving-average-price "DBC" {:window 252}))
                      [(weight-equal
                        [(if
                          (>
                           (moving-average-price "DBC" {:window 50})
                           (moving-average-price "DBC" {:window 100}))
                          [(weight-equal
                            [(if
                              (> (rsi "DBC" {:window 60}) 60)
                              [(asset
                                "SHV"
                                "iShares Short Treasury Bond ETF")]
                              [(asset
                                "DBC"
                                "Invesco DB Commodity Index Tracking Fund")])])]
                          [(asset
                            "SHV"
                            "iShares Short Treasury Bond ETF")])])]
                      [(asset
                        "SHV"
                        "iShares Short Treasury Bond ETF")])])])])])])])
         (group
          "(TMV/TMF/Gold Momentum)/BIORECKED"
          [(weight-equal
            [(group
              "TMF/TMV/Gold Momentum"
              [(weight-equal
                [(group
                  "TMV Momentum"
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
                               (moving-average-price
                                "TMV"
                                {:window 135}))
                              [(weight-equal
                                [(if
                                  (> (rsi "TMV" {:window 10}) 71)
                                  [(asset
                                    "SHV"
                                    "iShares Short Treasury Bond ETF")]
                                  [(weight-equal
                                    [(if
                                      (> (rsi "TMV" {:window 60}) 59)
                                      [(asset
                                        "TLT"
                                        "iShares 20+ Year Treasury Bond ETF")]
                                      [(asset
                                        "TMV"
                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                              [(asset
                                "BND"
                                "Vanguard Total Bond Market ETF")])])]
                          [(asset
                            "BND"
                            "Vanguard Total Bond Market ETF")])])])])])
                 (group
                  "TMF Momentum"
                  [(weight-specified
                    1
                    (if
                     (< (rsi "TMF" {:window 10}) 32)
                     [(asset
                       "TMF"
                       "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                     [(weight-equal
                       [(if
                         (>
                          (moving-average-price "TLT" {:window 15})
                          (moving-average-price "TLT" {:window 50}))
                         [(weight-equal
                           [(if
                             (> (rsi "TMF" {:window 10}) 72)
                             [(asset
                               "SHV"
                               "iShares Short Treasury Bond ETF")]
                             [(weight-equal
                               [(if
                                 (> (rsi "TMF" {:window 60}) 57)
                                 [(asset
                                   "TBF"
                                   "Proshares Short 20+ Year Treasury")]
                                 [(asset
                                   "TMF"
                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])]
                         [(asset
                           "SHV"
                           "iShares Short Treasury Bond ETF")])])]))])
                 (group
                  "Gold Momentum"
                  [(weight-equal
                    [(if
                      (>
                       (moving-average-price "GLD" {:window 200})
                       (moving-average-price "GLD" {:window 350}))
                      [(weight-equal
                        [(if
                          (>
                           (moving-average-price "GLD" {:window 60})
                           (moving-average-price "GLD" {:window 150}))
                          [(asset "GLD" nil)]
                          [(asset "SHV" nil)])])]
                      [(asset "SHV" nil)])])])])])
             (group
              "BIOTECH + TECH"
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
                          [(group
                            "A Better \"Buy the Dips Nasdaq\" by Garen Phillips"
                            [(weight-equal
                              [(if
                                (<
                                 (cumulative-return "QQQ" {:window 5})
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
                                      "ProShares UltraPro Short QQQ")]
                                    [(weight-equal
                                      [(if
                                        (>
                                         (rsi "TQQQ" {:window 10})
                                         31)
                                        [(asset
                                          "SQQQ"
                                          "ProShares UltraPro Short QQQ")]
                                        [(asset
                                          "LABU"
                                          "Direxion Daily S&P Biotech Bull 3X Shares")])])])])]
                                [(weight-equal
                                  [(if
                                    (> (rsi "QQQ" {:window 10}) 80)
                                    [(asset
                                      "SQQQ"
                                      "ProShares UltraPro Short QQQ")]
                                    [(weight-equal
                                      [(if
                                        (< (rsi "QQQ" {:window 10}) 31)
                                        [(asset
                                          "LABU"
                                          "Direxion Daily S&P Biotech Bull 3X Shares")]
                                        [(group
                                          "A Better QQQ"
                                          [(weight-equal
                                            [(weight-equal
                                              [(asset
                                                "TQQQ"
                                                "ProShares UltraPro QQQ")
                                               (asset
                                                "TSM"
                                                "Taiwan Semiconductor Manufacturing Co., Ltd. Sponsored ADR")
                                               (asset
                                                "MSFT"
                                                "Microsoft Corporation")
                                               (asset
                                                "AMZN"
                                                "Amazon.com, Inc.")
                                               (asset
                                                "AAPL"
                                                "Apple Inc.")
                                               (asset
                                                "AMD"
                                                "Advanced Micro Devices, Inc.")
                                               (asset
                                                "NVDA"
                                                "NVIDIA Corporation")
                                               (asset
                                                "TSLA"
                                                "Tesla Inc")])])])])])])])])])])])])])])]
                  [(weight-equal
                    [(if
                      (< (rsi "TQQQ" {:window 10}) 31)
                      [(asset
                        "LABU"
                        "Direxion Daily S&P Biotech Bull 3X Shares")]
                      [(weight-equal
                        [(if
                          (< (rsi "SPY" {:window 10}) 30)
                          [(asset
                            "LABU"
                            "Direxion Daily S&P Biotech Bull 3X Shares")]
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
                                        "SQQQ"
                                        "ProShares UltraPro Short QQQ")
                                       (asset
                                        "BSV"
                                        "Vanguard Short-Term Bond ETF")])])]
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
                                        "LABU"
                                        "Direxion Daily S&P Biotech Bull 3X Shares")])])]
                                  [(weight-equal
                                    [(filter
                                      (rsi {:window 10})
                                      (select-top 1)
                                      [(asset
                                        "SQQQ"
                                        "ProShares UltraPro Short QQQ")
                                       (asset
                                        "BSV"
                                        "Vanguard Short-Term Bond ETF")])])])])])])])])])])])])])])])])])])]))
