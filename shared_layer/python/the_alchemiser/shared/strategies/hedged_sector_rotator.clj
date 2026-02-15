(defsymphony
 "Hedged Sector Rotator "
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-specified
  0.6
  (if
   (> (rsi "XLK" {:window 10}) 80)
   [(asset "UVXY" "ProShares Ultra VIX Short-Term Futures ETF")]
   [(weight-equal
     [(if
       (> (rsi "XLF" {:window 10}) 80)
       [(asset "UVXY" "ProShares Ultra VIX Short-Term Futures ETF")]
       [(weight-equal
         [(if
           (> (rsi "XLV" {:window 10}) 80)
           [(asset
             "UVXY"
             "ProShares Ultra VIX Short-Term Futures ETF")]
           [(weight-equal
             [(if
               (> (rsi "XLE" {:window 10}) 80)
               [(asset
                 "UVXY"
                 "ProShares Ultra VIX Short-Term Futures ETF")]
               [(weight-equal
                 [(if
                   (> (rsi "XLB" {:window 10}) 80)
                   [(asset
                     "UVXY"
                     "ProShares Ultra VIX Short-Term Futures ETF")]
                   [(weight-equal
                     [(if
                       (> (rsi "XTL" {:window 10}) 80)
                       [(asset
                         "UVXY"
                         "ProShares Ultra VIX Short-Term Futures ETF")]
                       [(weight-equal
                         [(if
                           (> (rsi "XLRE" {:window 10}) 80)
                           [(asset
                             "UVXY"
                             "ProShares Ultra VIX Short-Term Futures ETF")]
                           [(weight-equal
                             [(if
                               (> (rsi "XLY" {:window 10}) 80)
                               [(asset
                                 "UVXY"
                                 "ProShares Ultra VIX Short-Term Futures ETF")]
                               [(weight-equal
                                 [(if
                                   (> (rsi "XLI" {:window 10}) 80)
                                   [(asset
                                     "UVXY"
                                     "ProShares Ultra VIX Short-Term Futures ETF")]
                                   [(weight-equal
                                     [(if
                                       (> (rsi "XLU" {:window 10}) 80)
                                       [(asset
                                         "UVXY"
                                         "ProShares Ultra VIX Short-Term Futures ETF")]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "XLP" {:window 10})
                                            80)
                                           [(asset
                                             "UVXY"
                                             "ProShares Ultra VIX Short-Term Futures ETF")]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "XLK"
                                                 {:window 10})
                                                30)
                                               [(group
                                                 "Technology"
                                                 [(weight-equal
                                                   [(filter
                                                     (moving-average-return
                                                      {:window 200})
                                                     (select-top 1)
                                                     [(asset
                                                       "XLK"
                                                       "Technology Select Sector SPDR Fund")
                                                      (asset
                                                       "TECL"
                                                       "Direxion Daily Technology Bull 3x Shares")
                                                      (asset
                                                       "SVXY"
                                                       "ProShares Short VIX Short-Term Futures ETF")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (<
                                                    (rsi
                                                     "XLF"
                                                     {:window 10})
                                                    30)
                                                   [(group
                                                     "Financials"
                                                     [(weight-equal
                                                       [(filter
                                                         (moving-average-return
                                                          {:window 10})
                                                         (select-top 1)
                                                         [(asset
                                                           "XLF"
                                                           "Financial Select Sector SPDR Fund")
                                                          (asset
                                                           "FAS"
                                                           "Direxion Daily Financial Bull 3x Shares")
                                                          (asset
                                                           "SVXY"
                                                           "ProShares Short VIX Short-Term Futures ETF")])])])]
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (rsi
                                                         "XLV"
                                                         {:window 10})
                                                        30)
                                                       [(group
                                                         "Healthcare"
                                                         [(weight-equal
                                                           [(filter
                                                             (moving-average-return
                                                              {:window
                                                               10})
                                                             (select-top
                                                              1)
                                                             [(asset
                                                               "XLV"
                                                               "Health Care Select Sector SPDR Fund")
                                                              (asset
                                                               "CURE"
                                                               "Direxion Daily Healthcare Bull 3x Shares")
                                                              (asset
                                                               "SVXY"
                                                               "ProShares Short VIX Short-Term Futures ETF")])])])]
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (rsi
                                                             "XLE"
                                                             {:window
                                                              10})
                                                            30)
                                                           [(group
                                                             "Energy"
                                                             [(weight-equal
                                                               [(filter
                                                                 (moving-average-return
                                                                  {:window
                                                                   10})
                                                                 (select-top
                                                                  1)
                                                                 [(asset
                                                                   "XLE"
                                                                   "Energy Select Sector SPDR Fund")
                                                                  (asset
                                                                   "ERX"
                                                                   "Direxion Daily Energy Bull 2x Shares")
                                                                  (asset
                                                                   "SVXY"
                                                                   "ProShares Short VIX Short-Term Futures ETF")])])])]
                                                           [(weight-equal
                                                             [(if
                                                               (<
                                                                (rsi
                                                                 "XLB"
                                                                 {:window
                                                                  10})
                                                                30)
                                                               [(group
                                                                 "Materials"
                                                                 [(weight-equal
                                                                   [(filter
                                                                     (moving-average-return
                                                                      {:window
                                                                       10})
                                                                     (select-top
                                                                      1)
                                                                     [(asset
                                                                       "XLB"
                                                                       "Materials Select Sector SPDR Fund")
                                                                      (asset
                                                                       "UYM"
                                                                       "ProShares Ultra Materials")
                                                                      (asset
                                                                       "SVXY"
                                                                       "ProShares Short VIX Short-Term Futures ETF")])])])]
                                                               [(weight-equal
                                                                 [(if
                                                                   (<
                                                                    (rsi
                                                                     "XTL"
                                                                     {:window
                                                                      10})
                                                                    30)
                                                                   [(group
                                                                     "Telecom"
                                                                     [(weight-equal
                                                                       [(filter
                                                                         (moving-average-return
                                                                          {:window
                                                                           10})
                                                                         (select-top
                                                                          1)
                                                                         [(asset
                                                                           "XTL"
                                                                           "SPDR S&P Telecom ETF")
                                                                          (asset
                                                                           "LTL"
                                                                           "ProShares Ultra Communication Services")
                                                                          (asset
                                                                           "SVXY"
                                                                           "ProShares Short VIX Short-Term Futures ETF")])])])]
                                                                   [(weight-equal
                                                                     [(if
                                                                       (<
                                                                        (rsi
                                                                         "XLRE"
                                                                         {:window
                                                                          10})
                                                                        30)
                                                                       [(group
                                                                         "Real Estate"
                                                                         [(weight-equal
                                                                           [(filter
                                                                             (moving-average-return
                                                                              {:window
                                                                               10})
                                                                             (select-top
                                                                              1)
                                                                             [(asset
                                                                               "XLRE"
                                                                               "Real Estate Select Sector SPDR Fund")
                                                                              (asset
                                                                               "DRN"
                                                                               "Direxion Daily Real Estate Bull 3x Shares")
                                                                              (asset
                                                                               "SVXY"
                                                                               "ProShares Short VIX Short-Term Futures ETF")])])])]
                                                                       [(weight-equal
                                                                         [(if
                                                                           (<
                                                                            (rsi
                                                                             "XLY"
                                                                             {:window
                                                                              10})
                                                                            30)
                                                                           [(group
                                                                             "Consumer Discretionary"
                                                                             [(weight-equal
                                                                               [(filter
                                                                                 (moving-average-return
                                                                                  {:window
                                                                                   10})
                                                                                 (select-top
                                                                                  1)
                                                                                 [(asset
                                                                                   "XLY"
                                                                                   "Consumer Discretionary Select Sector SPDR Fund")
                                                                                  (asset
                                                                                   "WANT"
                                                                                   "Direxion Daily Consumer Discretionary Bull 3x Shares")
                                                                                  (asset
                                                                                   "SVXY"
                                                                                   "ProShares Short VIX Short-Term Futures ETF")])])])]
                                                                           [(weight-equal
                                                                             [(if
                                                                               (<
                                                                                (rsi
                                                                                 "XLI"
                                                                                 {:window
                                                                                  10})
                                                                                30)
                                                                               [(group
                                                                                 "Industrials"
                                                                                 [(weight-equal
                                                                                   [(filter
                                                                                     (moving-average-return
                                                                                      {:window
                                                                                       10})
                                                                                     (select-top
                                                                                      1)
                                                                                     [(asset
                                                                                       "XLI"
                                                                                       "Industrial Select Sector SPDR Fund")
                                                                                      (asset
                                                                                       "DUSL"
                                                                                       "Direxion Daily Industrials Bull 3X Shares")
                                                                                      (asset
                                                                                       "SVXY"
                                                                                       "ProShares Short VIX Short-Term Futures ETF")])])])]
                                                                               [(weight-equal
                                                                                 [(if
                                                                                   (<
                                                                                    (rsi
                                                                                     "XLU"
                                                                                     {:window
                                                                                      10})
                                                                                    30)
                                                                                   [(group
                                                                                     "Utilities"
                                                                                     [(weight-equal
                                                                                       [(filter
                                                                                         (moving-average-return
                                                                                          {:window
                                                                                           10})
                                                                                         (select-top
                                                                                          1)
                                                                                         [(asset
                                                                                           "XLU"
                                                                                           "Utilities Select Sector SPDR Fund")
                                                                                          (asset
                                                                                           "UTSL"
                                                                                           "Direxion Daily Utilities Bull 3X Shares")
                                                                                          (asset
                                                                                           "SVXY"
                                                                                           "ProShares Short VIX Short-Term Futures ETF")])])])]
                                                                                   [(weight-equal
                                                                                     [(if
                                                                                       (<
                                                                                        (rsi
                                                                                         "XLP"
                                                                                         {:window
                                                                                          10})
                                                                                        30)
                                                                                       [(group
                                                                                         "Consumer Staples"
                                                                                         [(weight-equal
                                                                                           [(filter
                                                                                             (moving-average-return
                                                                                              {:window
                                                                                               10})
                                                                                             (select-top
                                                                                              1)
                                                                                             [(asset
                                                                                               "XLP"
                                                                                               "Consumer Staples Select Sector SPDR Fund")
                                                                                              (asset
                                                                                               "UGE"
                                                                                               "ProShares Ultra Consumer Staples")
                                                                                              (asset
                                                                                               "SVXY"
                                                                                               "ProShares Short VIX Short-Term Futures ETF")])])])]
                                                                                       [(weight-equal
                                                                                         [(filter
                                                                                           (stdev-return
                                                                                            {:window
                                                                                             10})
                                                                                           (select-top
                                                                                            1)
                                                                                           [(group
                                                                                             "Technology"
                                                                                             [(weight-equal
                                                                                               [(filter
                                                                                                 (moving-average-return
                                                                                                  {:window
                                                                                                   200})
                                                                                                 (select-top
                                                                                                  1)
                                                                                                 [(asset
                                                                                                   "XLK"
                                                                                                   "Technology Select Sector SPDR Fund")
                                                                                                  (asset
                                                                                                   "TECL"
                                                                                                   "Direxion Daily Technology Bull 3x Shares")])])])
                                                                                            (group
                                                                                             "Financials"
                                                                                             [(weight-equal
                                                                                               [(filter
                                                                                                 (moving-average-return
                                                                                                  {:window
                                                                                                   10})
                                                                                                 (select-top
                                                                                                  1)
                                                                                                 [(asset
                                                                                                   "XLF"
                                                                                                   "Financial Select Sector SPDR Fund")
                                                                                                  (asset
                                                                                                   "FAS"
                                                                                                   "Direxion Daily Financial Bull 3x Shares")])])])
                                                                                            (group
                                                                                             "Healthcare"
                                                                                             [(weight-equal
                                                                                               [(filter
                                                                                                 (moving-average-return
                                                                                                  {:window
                                                                                                   10})
                                                                                                 (select-top
                                                                                                  1)
                                                                                                 [(asset
                                                                                                   "XLV"
                                                                                                   "Health Care Select Sector SPDR Fund")
                                                                                                  (asset
                                                                                                   "CURE"
                                                                                                   "Direxion Daily Healthcare Bull 3x Shares")])])])
                                                                                            (group
                                                                                             "Energy"
                                                                                             [(weight-equal
                                                                                               [(filter
                                                                                                 (moving-average-return
                                                                                                  {:window
                                                                                                   10})
                                                                                                 (select-top
                                                                                                  1)
                                                                                                 [(asset
                                                                                                   "XLE"
                                                                                                   "Energy Select Sector SPDR Fund")
                                                                                                  (asset
                                                                                                   "ERX"
                                                                                                   "Direxion Daily Energy Bull 2x Shares")])])])
                                                                                            (group
                                                                                             "Materials"
                                                                                             [(weight-equal
                                                                                               [(filter
                                                                                                 (moving-average-return
                                                                                                  {:window
                                                                                                   10})
                                                                                                 (select-top
                                                                                                  1)
                                                                                                 [(asset
                                                                                                   "XLB"
                                                                                                   "Materials Select Sector SPDR Fund")
                                                                                                  (asset
                                                                                                   "UYM"
                                                                                                   "ProShares Ultra Materials")])])])
                                                                                            (group
                                                                                             "Telecom"
                                                                                             [(weight-equal
                                                                                               [(filter
                                                                                                 (moving-average-return
                                                                                                  {:window
                                                                                                   10})
                                                                                                 (select-top
                                                                                                  1)
                                                                                                 [(asset
                                                                                                   "XTL"
                                                                                                   "SPDR S&P Telecom ETF")
                                                                                                  (asset
                                                                                                   "LTL"
                                                                                                   "ProShares Ultra Communication Services")])])])
                                                                                            (group
                                                                                             "Real Estate"
                                                                                             [(weight-equal
                                                                                               [(filter
                                                                                                 (moving-average-return
                                                                                                  {:window
                                                                                                   10})
                                                                                                 (select-top
                                                                                                  1)
                                                                                                 [(asset
                                                                                                   "XLRE"
                                                                                                   "Real Estate Select Sector SPDR Fund")
                                                                                                  (asset
                                                                                                   "DRN"
                                                                                                   "Direxion Daily Real Estate Bull 3x Shares")])])])
                                                                                            (group
                                                                                             "Consumer Discretionary"
                                                                                             [(weight-equal
                                                                                               [(filter
                                                                                                 (moving-average-return
                                                                                                  {:window
                                                                                                   10})
                                                                                                 (select-top
                                                                                                  1)
                                                                                                 [(asset
                                                                                                   "XLY"
                                                                                                   "Consumer Discretionary Select Sector SPDR Fund")
                                                                                                  (asset
                                                                                                   "WANT"
                                                                                                   "Direxion Daily Consumer Discretionary Bull 3x Shares")])])])
                                                                                            (group
                                                                                             "Industrials"
                                                                                             [(weight-equal
                                                                                               [(filter
                                                                                                 (moving-average-return
                                                                                                  {:window
                                                                                                   10})
                                                                                                 (select-top
                                                                                                  1)
                                                                                                 [(asset
                                                                                                   "XLI"
                                                                                                   "Industrial Select Sector SPDR Fund")
                                                                                                  (asset
                                                                                                   "DUSL"
                                                                                                   "Direxion Daily Industrials Bull 3X Shares")])])])
                                                                                            (group
                                                                                             "Utilities"
                                                                                             [(weight-equal
                                                                                               [(filter
                                                                                                 (moving-average-return
                                                                                                  {:window
                                                                                                   10})
                                                                                                 (select-top
                                                                                                  1)
                                                                                                 [(asset
                                                                                                   "XLU"
                                                                                                   "Utilities Select Sector SPDR Fund")
                                                                                                  (asset
                                                                                                   "UTSL"
                                                                                                   "Direxion Daily Utilities Bull 3X Shares")])])])
                                                                                            (group
                                                                                             "Consumer Staples"
                                                                                             [(weight-equal
                                                                                               [(filter
                                                                                                 (moving-average-return
                                                                                                  {:window
                                                                                                   10})
                                                                                                 (select-top
                                                                                                  1)
                                                                                                 [(asset
                                                                                                   "XLP"
                                                                                                   "Consumer Staples Select Sector SPDR Fund")
                                                                                                  (asset
                                                                                                   "UGE"
                                                                                                   "ProShares Ultra Consumer Staples")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
      (if
       (< (rsi "XLK" {:window 10}) 30)
       [(group
         "Technology"
         [(weight-equal
           [(filter
             (moving-average-return {:window 200})
             (select-top 1)
             [(asset "XLK" "Technology Select Sector SPDR Fund")
              (asset "TECL" "Direxion Daily Technology Bull 3x Shares")
              (asset
               "SVXY"
               "ProShares Short VIX Short-Term Futures ETF")])])])]
       [(weight-equal
         [(if
           (< (rsi "XLF" {:window 10}) 30)
           [(group
             "Financials"
             [(weight-equal
               [(filter
                 (moving-average-return {:window 10})
                 (select-top 1)
                 [(asset "XLF" "Financial Select Sector SPDR Fund")
                  (asset
                   "FAS"
                   "Direxion Daily Financial Bull 3x Shares")
                  (asset
                   "SVXY"
                   "ProShares Short VIX Short-Term Futures ETF")])])])]
           [(weight-equal
             [(if
               (< (rsi "XLV" {:window 10}) 30)
               [(group
                 "Healthcare"
                 [(weight-equal
                   [(filter
                     (moving-average-return {:window 10})
                     (select-top 1)
                     [(asset
                       "XLV"
                       "Health Care Select Sector SPDR Fund")
                      (asset
                       "CURE"
                       "Direxion Daily Healthcare Bull 3x Shares")
                      (asset
                       "SVXY"
                       "ProShares Short VIX Short-Term Futures ETF")])])])]
               [(weight-equal
                 [(if
                   (< (rsi "XLE" {:window 10}) 30)
                   [(group
                     "Energy"
                     [(weight-equal
                       [(filter
                         (moving-average-return {:window 10})
                         (select-top 1)
                         [(asset
                           "XLE"
                           "Energy Select Sector SPDR Fund")
                          (asset
                           "ERX"
                           "Direxion Daily Energy Bull 2x Shares")
                          (asset
                           "SVXY"
                           "ProShares Short VIX Short-Term Futures ETF")])])])]
                   [(weight-equal
                     [(if
                       (< (rsi "XLB" {:window 10}) 30)
                       [(group
                         "Materials"
                         [(weight-equal
                           [(filter
                             (moving-average-return {:window 10})
                             (select-top 1)
                             [(asset
                               "XLB"
                               "Materials Select Sector SPDR Fund")
                              (asset "UYM" "ProShares Ultra Materials")
                              (asset
                               "SVXY"
                               "ProShares Short VIX Short-Term Futures ETF")])])])]
                       [(weight-equal
                         [(if
                           (< (rsi "XTL" {:window 10}) 30)
                           [(group
                             "Telecom"
                             [(weight-equal
                               [(filter
                                 (moving-average-return {:window 10})
                                 (select-top 1)
                                 [(asset "XTL" "SPDR S&P Telecom ETF")
                                  (asset
                                   "LTL"
                                   "ProShares Ultra Communication Services")
                                  (asset
                                   "SVXY"
                                   "ProShares Short VIX Short-Term Futures ETF")])])])]
                           [(weight-equal
                             [(if
                               (< (rsi "XLRE" {:window 10}) 30)
                               [(group
                                 "Real Estate"
                                 [(weight-equal
                                   [(filter
                                     (moving-average-return
                                      {:window 10})
                                     (select-top 1)
                                     [(asset
                                       "XLRE"
                                       "Real Estate Select Sector SPDR Fund")
                                      (asset
                                       "DRN"
                                       "Direxion Daily Real Estate Bull 3x Shares")
                                      (asset
                                       "SVXY"
                                       "ProShares Short VIX Short-Term Futures ETF")])])])]
                               [(weight-equal
                                 [(if
                                   (< (rsi "XLY" {:window 10}) 30)
                                   [(group
                                     "Consumer Discretionary"
                                     [(weight-equal
                                       [(filter
                                         (moving-average-return
                                          {:window 10})
                                         (select-top 1)
                                         [(asset
                                           "XLY"
                                           "Consumer Discretionary Select Sector SPDR Fund")
                                          (asset
                                           "WANT"
                                           "Direxion Daily Consumer Discretionary Bull 3x Shares")
                                          (asset
                                           "SVXY"
                                           "ProShares Short VIX Short-Term Futures ETF")])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "XLI" {:window 10}) 30)
                                       [(group
                                         "Industrials"
                                         [(weight-equal
                                           [(filter
                                             (moving-average-return
                                              {:window 10})
                                             (select-top 1)
                                             [(asset
                                               "XLI"
                                               "Industrial Select Sector SPDR Fund")
                                              (asset
                                               "DUSL"
                                               "Direxion Daily Industrials Bull 3X Shares")
                                              (asset
                                               "SVXY"
                                               "ProShares Short VIX Short-Term Futures ETF")])])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "XLU" {:window 10})
                                            30)
                                           [(group
                                             "Utilities"
                                             [(weight-equal
                                               [(filter
                                                 (moving-average-return
                                                  {:window 10})
                                                 (select-top 1)
                                                 [(asset
                                                   "XLU"
                                                   "Utilities Select Sector SPDR Fund")
                                                  (asset
                                                   "UTSL"
                                                   "Direxion Daily Utilities Bull 3X Shares")
                                                  (asset
                                                   "SVXY"
                                                   "ProShares Short VIX Short-Term Futures ETF")])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "XLP"
                                                 {:window 10})
                                                30)
                                               [(group
                                                 "Consumer Staples"
                                                 [(weight-equal
                                                   [(filter
                                                     (moving-average-return
                                                      {:window 10})
                                                     (select-top 1)
                                                     [(asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")
                                                      (asset
                                                       "UGE"
                                                       "ProShares Ultra Consumer Staples")
                                                      (asset
                                                       "SVXY"
                                                       "ProShares Short VIX Short-Term Futures ETF")])])])]
                                               [(weight-equal
                                                 [(filter
                                                   (cumulative-return
                                                    {:window 30})
                                                   (select-top 1)
                                                   [(group
                                                     "Technology"
                                                     [(weight-equal
                                                       [(filter
                                                         (moving-average-return
                                                          {:window
                                                           200})
                                                         (select-top 1)
                                                         [(asset
                                                           "XLK"
                                                           "Technology Select Sector SPDR Fund")
                                                          (asset
                                                           "TECL"
                                                           "Direxion Daily Technology Bull 3x Shares")])])])
                                                    (group
                                                     "Financials"
                                                     [(weight-equal
                                                       [(filter
                                                         (moving-average-return
                                                          {:window
                                                           200})
                                                         (select-top 1)
                                                         [(asset
                                                           "XLF"
                                                           "Financial Select Sector SPDR Fund")
                                                          (asset
                                                           "FAS"
                                                           "Direxion Daily Financial Bull 3x Shares")])])])
                                                    (group
                                                     "Healthcare"
                                                     [(weight-equal
                                                       [(filter
                                                         (moving-average-return
                                                          {:window
                                                           200})
                                                         (select-top 1)
                                                         [(asset
                                                           "XLV"
                                                           "Health Care Select Sector SPDR Fund")
                                                          (asset
                                                           "CURE"
                                                           "Direxion Daily Healthcare Bull 3x Shares")])])])
                                                    (group
                                                     "Energy"
                                                     [(weight-equal
                                                       [(filter
                                                         (moving-average-return
                                                          {:window
                                                           200})
                                                         (select-top 1)
                                                         [(asset
                                                           "XLE"
                                                           "Energy Select Sector SPDR Fund")
                                                          (asset
                                                           "ERX"
                                                           "Direxion Daily Energy Bull 2x Shares")])])])
                                                    (group
                                                     "Materials"
                                                     [(weight-equal
                                                       [(filter
                                                         (moving-average-return
                                                          {:window
                                                           200})
                                                         (select-top 1)
                                                         [(asset
                                                           "XLB"
                                                           "Materials Select Sector SPDR Fund")
                                                          (asset
                                                           "UYM"
                                                           "ProShares Ultra Materials")])])])
                                                    (group
                                                     "Telecom"
                                                     [(weight-equal
                                                       [(filter
                                                         (moving-average-return
                                                          {:window
                                                           200})
                                                         (select-top 1)
                                                         [(asset
                                                           "XTL"
                                                           "SPDR S&P Telecom ETF")
                                                          (asset
                                                           "LTL"
                                                           "ProShares Ultra Communication Services")])])])
                                                    (group
                                                     "Real Estate"
                                                     [(weight-equal
                                                       [(filter
                                                         (moving-average-return
                                                          {:window
                                                           200})
                                                         (select-top 1)
                                                         [(asset
                                                           "XLRE"
                                                           "Real Estate Select Sector SPDR Fund")
                                                          (asset
                                                           "DRN"
                                                           "Direxion Daily Real Estate Bull 3x Shares")])])])
                                                    (group
                                                     "Consumer Discretionary"
                                                     [(weight-equal
                                                       [(filter
                                                         (moving-average-return
                                                          {:window
                                                           200})
                                                         (select-top 1)
                                                         [(asset
                                                           "XLY"
                                                           "Consumer Discretionary Select Sector SPDR Fund")
                                                          (asset
                                                           "WANT"
                                                           "Direxion Daily Consumer Discretionary Bull 3x Shares")])])])
                                                    (group
                                                     "Industrials"
                                                     [(weight-equal
                                                       [(filter
                                                         (moving-average-return
                                                          {:window
                                                           200})
                                                         (select-top 1)
                                                         [(asset
                                                           "XLI"
                                                           "Industrial Select Sector SPDR Fund")
                                                          (asset
                                                           "DUSL"
                                                           "Direxion Daily Industrials Bull 3X Shares")])])])
                                                    (group
                                                     "Utilities"
                                                     [(weight-equal
                                                       [(filter
                                                         (moving-average-return
                                                          {:window
                                                           200})
                                                         (select-top 1)
                                                         [(asset
                                                           "XLU"
                                                           "Utilities Select Sector SPDR Fund")
                                                          (asset
                                                           "UTSL"
                                                           "Direxion Daily Utilities Bull 3X Shares")])])])
                                                    (group
                                                     "Consumer Staples"
                                                     [(weight-equal
                                                       [(filter
                                                         (moving-average-return
                                                          {:window
                                                           200})
                                                         (select-top 1)
                                                         [(asset
                                                           "XLP"
                                                           "Consumer Staples Select Sector SPDR Fund")
                                                          (asset
                                                           "UGE"
                                                           "ProShares Ultra Consumer Staples")])])])])])])])])])])])])])])])])])])])])])])])])])])])])
  0.4
  (weight-equal
   [(group
     "DereckN Hedge System"
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
                      (moving-average-price "TMV" {:window 135}))
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
            (> (rsi "QQQ" {:window 10}) 80)
            [(asset "VIXY" "ProShares VIX Short-Term Futures ETF")]
            [(weight-equal
              [(if
                (> (rsi "SPY" {:window 10}) 80)
                [(asset "VIXY" "ProShares VIX Short-Term Futures ETF")]
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
                             (moving-average-price "TMF" {:window 10}))
                            [(weight-equal
                              [(if
                                (> (rsi "TMF" {:window 10}) 72)
                                [(asset
                                  "SHV"
                                  "iShares Short Treasury Bond ETF")]
                                [(weight-equal
                                  [(asset
                                    "TMF"
                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])]
                            [(weight-equal
                              [(if
                                (< (rsi "TQQQ" {:window 10}) 31)
                                [(asset
                                  "TECL"
                                  "Direxion Daily Technology Bull 3x Shares")]
                                [(weight-equal
                                  [(asset
                                    "SHV"
                                    "iShares Short Treasury Bond ETF")])])])])])]
                        [(weight-equal
                          [(if
                            (< (rsi "TQQQ" {:window 10}) 31)
                            [(asset
                              "TECL"
                              "Direxion Daily Technology Bull 3x Shares")]
                            [(weight-equal
                              [(asset
                                "SHV"
                                "iShares Short Treasury Bond ETF")])])])])])])])])])]))])
        (group
         "SVXY FTLT"
         [(weight-equal
           [(if
             (> (rsi "QQQ" {:window 10}) 80)
             [(asset "VIXY" "ProShares VIX Short-Term Futures ETF")]
             [(weight-equal
               [(if
                 (> (rsi "SPY" {:window 10}) 80)
                 [(asset
                   "VIXY"
                   "ProShares VIX Short-Term Futures ETF")]
                 [(weight-equal
                   [(if
                     (< (rsi "QQQ" {:window 10}) 30)
                     [(asset
                       "XLK"
                       "Technology Select Sector SPDR Fund")]
                     [(weight-equal
                       [(if
                         (>
                          (current-price "SVXY")
                          (moving-average-price "SVXY" {:window 24}))
                         [(weight-equal
                           [(filter
                             (moving-average-return {:window 20})
                             (select-top 1)
                             [(asset
                               "SVXY"
                               "ProShares Short VIX Short-Term Futures ETF")
                              (asset
                               "VTI"
                               "Vanguard Total Stock Market ETF")])])]
                         [(weight-equal
                           [(asset
                             "BTAL"
                             "AGF U.S. Market Neutral Anti-Beta Fund")])])])])])])])])])])
        (group
         "TINA"
         [(weight-equal
           [(if
             (>
              (current-price "QQQ")
              (moving-average-price "QQQ" {:window 20}))
             [(weight-equal
               [(if
                 (> (cumulative-return "QQQ" {:window 10}) 5.5)
                 [(asset "PSQ" "ProShares Short QQQ")]
                 [(weight-equal
                   [(if
                     (< (cumulative-return "TQQQ" {:window 62}) -33)
                     [(asset "TQQQ" "ProShares UltraPro QQQ")]
                     [(weight-equal
                       [(asset
                         "SHV"
                         "iShares Short Treasury Bond ETF")])])])])])]
             [(weight-equal
               [(if
                 (< (rsi "QQQ" {:window 10}) 30)
                 [(asset
                   "TECL"
                   "Direxion Daily Technology Bull 3x Shares")]
                 [(weight-equal
                   [(if
                     (< (cumulative-return "TQQQ" {:window 62}) -33)
                     [(asset "TQQQ" "ProShares UltraPro QQQ")]
                     [(weight-equal
                       [(filter
                         (rsi {:window 20})
                         (select-top 1)
                         [(asset "PSQ" "ProShares Short QQQ")
                          (asset "BSV" "Vanguard Short-Term Bond ETF")
                          (asset
                           "TLT"
                           "iShares 20+ Year Treasury Bond ETF")])])])])])])])])])
        (group
         "Shorting SPY"
         [(weight-equal
           [(group
             "20d BND vs 60d SH Logic To Go Short"
             [(weight-equal
               [(if
                 (> (rsi "BND" {:window 20}) (rsi "SH" {:window 60}))
                 [(weight-equal
                   [(if
                     (>
                      (current-price "SPY")
                      (moving-average-price "SPY" {:window 200}))
                     [(weight-equal
                       [(asset
                         "SHV"
                         "iShares Short Treasury Bond ETF")])]
                     [(weight-equal
                       [(if
                         (< (rsi "QQQ" {:window 10}) 30)
                         [(asset
                           "XLK"
                           "Technology Select Sector SPDR Fund")]
                         [(asset
                           "SHV"
                           "iShares Short Treasury Bond ETF")])])])])]
                 [(weight-equal
                   [(if
                     (< (rsi "QQQ" {:window 10}) 30)
                     [(asset
                       "XLK"
                       "Technology Select Sector SPDR Fund")]
                     [(weight-equal
                       [(if
                         (<
                          (exponential-moving-average-price
                           "SPY"
                           {:window 10})
                          (moving-average-price "SPY" {:window 10}))
                         [(asset "SH" "ProShares Short S&P500")]
                         [(asset
                           "SHV"
                           "iShares Short Treasury Bond ETF")])])])])])])])])])
        (group
         "SVXY FTLT | V2"
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
                     (< (rsi "QQQ" {:window 10}) 30)
                     [(asset
                       "XLK"
                       "Technology Select Sector SPDR Fund")]
                     [(weight-equal
                       [(if
                         (>
                          (current-price "SVXY")
                          (moving-average-price "SVXY" {:window 21}))
                         [(weight-specified
                           0.7
                           (filter
                            (moving-average-return {:window 20})
                            (select-top 1)
                            [(asset
                              "SVXY"
                              "ProShares Short VIX Short-Term Futures ETF")
                             (asset
                              "VTI"
                              "Vanguard Total Stock Market ETF")])
                           0.3
                           (weight-equal
                            [(asset
                              "VIXM"
                              "ProShares VIX Mid-Term Futures ETF")]))]
                         [(weight-equal
                           [(filter
                             (moving-average-return {:window 20})
                             (select-top 1)
                             [(asset
                               "BTAL"
                               "AGF U.S. Market Neutral Anti-Beta Fund")])])])])])])])])])])])])])])))
