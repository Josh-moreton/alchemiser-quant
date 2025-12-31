(defsymphony
 "Rain's Core Catalysts"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-specified
  0.75
  (group
   "Aggressive Leveraged VIX/Long Frontrunner (90,18,2012)"
   [(weight-equal
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
                                                (asset
                                                 "XLU"
                                                 nil)])])])]
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
                                                (asset
                                                 "XLU"
                                                 nil)])])])]
                                         [(asset
                                           "TECL"
                                           "Direxion Shares ETF Trust - Direxion Daily Technology Bull 3X Shares")])])])])])])])]
                           [(weight-specified
                             0.75
                             (if
                              (> (rsi "VTV" {:window 10}) 79)
                              [(asset
                                "VIXY"
                                "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
                              [(weight-equal
                                [(if
                                  (> (rsi "XLF" {:window 10}) 80)
                                  [(asset
                                    "VIXY"
                                    "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
                                  [(weight-equal
                                    [(if
                                      (> (rsi "XLY" {:window 10}) 80)
                                      [(asset
                                        "VIXY"
                                        "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
                                      [(group
                                        "Rain's Unified Signals: TQQQ FTLT, Holy Grail & KMLM"
                                        [(weight-equal
                                          [(group
                                            "SPY 200 DMA"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (current-price "SPY")
                                                 (moving-average-price
                                                  "SPY"
                                                  {:window 200}))
                                                [(weight-equal
                                                  [(if
                                                    (<
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 3})
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(group
                                                      "Bull Cross "
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           2)
                                                          [(asset
                                                            "TQQQ"
                                                            nil)
                                                           (asset
                                                            "TECL"
                                                            nil)
                                                           (asset
                                                            "SPXL"
                                                            nil)
                                                           (asset
                                                            "TMF"
                                                            nil)])])])]
                                                    [(weight-specified
                                                      0.2
                                                      (group
                                                       "SPY on Bonds | 20d AGG vs 60d SH"
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
                                                                (current-price
                                                                 "SPY")
                                                                (moving-average-price
                                                                 "SPY"
                                                                 {:window
                                                                  30}))
                                                               [(group
                                                                 "Conflict Check - KMLM Fund Surfing"
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
                                                                       [(asset
                                                                         "TQQQ"
                                                                         nil)
                                                                        (filter
                                                                         (moving-average-return
                                                                          {:window
                                                                           15})
                                                                         (select-top
                                                                          2)
                                                                         [(asset
                                                                           "TQQQ"
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
                                                                           15})
                                                                         (select-top
                                                                          1)
                                                                         [(asset
                                                                           "TQQQ"
                                                                           nil)
                                                                          (asset
                                                                           "TECL"
                                                                           nil)])])]
                                                                     [(group
                                                                       "Safe Sectors or Bonds"
                                                                       [(weight-equal
                                                                         [(filter
                                                                           (rsi
                                                                            {:window
                                                                             10})
                                                                           (select-bottom
                                                                            1)
                                                                           [(asset
                                                                             "BSV"
                                                                             nil)
                                                                            (asset
                                                                             "TLT"
                                                                             nil)
                                                                            (asset
                                                                             "LQD"
                                                                             nil)
                                                                            (asset
                                                                             "VBF"
                                                                             nil)
                                                                            (asset
                                                                             "XLP"
                                                                             nil)
                                                                            (asset
                                                                             "UGE"
                                                                             nil)
                                                                            (asset
                                                                             "XLV"
                                                                             nil)
                                                                            (asset
                                                                             "XLU"
                                                                             nil)])])])])])])]
                                                               [(group
                                                                 "Safe Sectors or Bonds"
                                                                 [(weight-equal
                                                                   [(filter
                                                                     (rsi
                                                                      {:window
                                                                       10})
                                                                     (select-bottom
                                                                      1)
                                                                     [(asset
                                                                       "BSV"
                                                                       nil)
                                                                      (asset
                                                                       "TLT"
                                                                       nil)
                                                                      (asset
                                                                       "LQD"
                                                                       nil)
                                                                      (asset
                                                                       "VBF"
                                                                       nil)
                                                                      (asset
                                                                       "XLP"
                                                                       nil)
                                                                      (asset
                                                                       "UGE"
                                                                       nil)
                                                                      (asset
                                                                       "XLV"
                                                                       nil)
                                                                      (asset
                                                                       "XLU"
                                                                       nil)])])])])])]
                                                           [(group
                                                             "Safe Sectors or Bonds"
                                                             [(weight-equal
                                                               [(filter
                                                                 (rsi
                                                                  {:window
                                                                   10})
                                                                 (select-bottom
                                                                  1)
                                                                 [(asset
                                                                   "BSV"
                                                                   nil)
                                                                  (asset
                                                                   "TLT"
                                                                   nil)
                                                                  (asset
                                                                   "LQD"
                                                                   nil)
                                                                  (asset
                                                                   "VBF"
                                                                   nil)
                                                                  (asset
                                                                   "XLP"
                                                                   nil)
                                                                  (asset
                                                                   "UGE"
                                                                   nil)
                                                                  (asset
                                                                   "XLV"
                                                                   nil)
                                                                  (asset
                                                                   "XLU"
                                                                   nil)])])])])])])
                                                      0.2
                                                      (group
                                                       "SPY on Staples | 20d XLP vs 20d SH"
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (rsi
                                                             "XLP"
                                                             {:window
                                                              20})
                                                            (rsi
                                                             "SH"
                                                             {:window
                                                              20}))
                                                           [(group
                                                             "Conflict Check - KMLM Fund Surfing"
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
                                                                   [(asset
                                                                     "TQQQ"
                                                                     nil)
                                                                    (filter
                                                                     (rsi
                                                                      {:window
                                                                       10})
                                                                     (select-bottom
                                                                      2)
                                                                     [(asset
                                                                       "TQQQ"
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
                                                                     (rsi
                                                                      {:window
                                                                       10})
                                                                     (select-bottom
                                                                      1)
                                                                     [(asset
                                                                       "TQQQ"
                                                                       nil)
                                                                      (asset
                                                                       "TECL"
                                                                       nil)])])]
                                                                 [(group
                                                                   "Safe Sectors or Bonds"
                                                                   [(weight-equal
                                                                     [(filter
                                                                       (rsi
                                                                        {:window
                                                                         10})
                                                                       (select-bottom
                                                                        1)
                                                                       [(asset
                                                                         "BSV"
                                                                         nil)
                                                                        (asset
                                                                         "TLT"
                                                                         nil)
                                                                        (asset
                                                                         "LQD"
                                                                         nil)
                                                                        (asset
                                                                         "VBF"
                                                                         nil)
                                                                        (asset
                                                                         "XLP"
                                                                         nil)
                                                                        (asset
                                                                         "UGE"
                                                                         nil)
                                                                        (asset
                                                                         "XLV"
                                                                         nil)
                                                                        (asset
                                                                         "XLU"
                                                                         nil)])])])])])])]
                                                           [(group
                                                             "Safe Sectors or Bonds"
                                                             [(weight-equal
                                                               [(filter
                                                                 (rsi
                                                                  {:window
                                                                   10})
                                                                 (select-bottom
                                                                  1)
                                                                 [(asset
                                                                   "BSV"
                                                                   nil)
                                                                  (asset
                                                                   "TLT"
                                                                   nil)
                                                                  (asset
                                                                   "LQD"
                                                                   nil)
                                                                  (asset
                                                                   "VBF"
                                                                   nil)
                                                                  (asset
                                                                   "XLP"
                                                                   nil)
                                                                  (asset
                                                                   "UGE"
                                                                   nil)
                                                                  (asset
                                                                   "XLV"
                                                                   nil)
                                                                  (asset
                                                                   "XLU"
                                                                   nil)])])])])])])
                                                      0.2
                                                      (group
                                                       "A Better \"Buy the Dips Nasdaq\" by Garen Phillips | Safe Sectors Mod"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "QQQ"
                                                             {:window
                                                              5})
                                                            -6)
                                                           [(group
                                                             "Conflict Check: KMLM Fund Surfing"
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
                                                                   "Safe Sectors or Bonds"
                                                                   [(weight-equal
                                                                     [(filter
                                                                       (rsi
                                                                        {:window
                                                                         10})
                                                                       (select-bottom
                                                                        1)
                                                                       [(asset
                                                                         "BSV"
                                                                         nil)
                                                                        (asset
                                                                         "TLT"
                                                                         nil)
                                                                        (asset
                                                                         "LQD"
                                                                         nil)
                                                                        (asset
                                                                         "VBF"
                                                                         nil)
                                                                        (asset
                                                                         "XLP"
                                                                         nil)
                                                                        (asset
                                                                         "UGE"
                                                                         nil)
                                                                        (asset
                                                                         "XLV"
                                                                         nil)
                                                                        (asset
                                                                         "XLU"
                                                                         nil)])])])]
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "SQQQ"
                                                                     nil)
                                                                    (filter
                                                                     (moving-average-return
                                                                      {:window
                                                                       15})
                                                                     (select-bottom
                                                                      2)
                                                                     [(asset
                                                                       "SQQQ"
                                                                       nil)
                                                                      (asset
                                                                       "SQQQ"
                                                                       nil)
                                                                      (asset
                                                                       "TECS"
                                                                       nil)
                                                                      (asset
                                                                       "SOXS"
                                                                       nil)])])])])])]
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (stdev-return
                                                                 "TQQQ"
                                                                 {:window
                                                                  10})
                                                                5)
                                                               [(group
                                                                 "Safe Sectors or Bonds"
                                                                 [(weight-equal
                                                                   [(filter
                                                                     (rsi
                                                                      {:window
                                                                       10})
                                                                     (select-bottom
                                                                      1)
                                                                     [(asset
                                                                       "BSV"
                                                                       nil)
                                                                      (asset
                                                                       "TLT"
                                                                       nil)
                                                                      (asset
                                                                       "LQD"
                                                                       nil)
                                                                      (asset
                                                                       "VBF"
                                                                       nil)
                                                                      (asset
                                                                       "XLP"
                                                                       nil)
                                                                      (asset
                                                                       "UGE"
                                                                       nil)
                                                                      (asset
                                                                       "XLV"
                                                                       nil)
                                                                      (asset
                                                                       "XLU"
                                                                       nil)])])])]
                                                               [(weight-equal
                                                                 [(asset
                                                                   "TQQQ"
                                                                   nil)
                                                                  (filter
                                                                   (moving-average-return
                                                                    {:window
                                                                     10})
                                                                   (select-top
                                                                    2)
                                                                   [(asset
                                                                     "TQQQ"
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
                                                                   (select-top
                                                                    1)
                                                                   [(asset
                                                                     "TQQQ"
                                                                     nil)
                                                                    (asset
                                                                     "TECL"
                                                                     nil)])])])])])])])
                                                      0.4
                                                      (group
                                                       "KMLM Fund Surfing"
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
                                                             [(weight-equal
                                                               [(asset
                                                                 "TQQQ"
                                                                 nil)
                                                                (filter
                                                                 (rsi
                                                                  {:window
                                                                   10})
                                                                 (select-bottom
                                                                  2)
                                                                 [(asset
                                                                   "TQQQ"
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
                                                                 (rsi
                                                                  {:window
                                                                   10})
                                                                 (select-bottom
                                                                  1)
                                                                 [(asset
                                                                   "TQQQ"
                                                                   nil)
                                                                  (asset
                                                                   "TECL"
                                                                   nil)])])
                                                              (group
                                                               "Conflict Check - A Better \"Buy the Dips Nasdaq\" by Garen Phillips | Safe Sectors Mod"
                                                               [(weight-equal
                                                                 [(if
                                                                   (<
                                                                    (cumulative-return
                                                                     "QQQ"
                                                                     {:window
                                                                      5})
                                                                    -6)
                                                                   [(group
                                                                     "Safe Sectors or Bonds"
                                                                     [(weight-equal
                                                                       [(filter
                                                                         (rsi
                                                                          {:window
                                                                           10})
                                                                         (select-bottom
                                                                          1)
                                                                         [(asset
                                                                           "BSV"
                                                                           nil)
                                                                          (asset
                                                                           "TLT"
                                                                           nil)
                                                                          (asset
                                                                           "LQD"
                                                                           nil)
                                                                          (asset
                                                                           "VBF"
                                                                           nil)
                                                                          (asset
                                                                           "XLP"
                                                                           nil)
                                                                          (asset
                                                                           "UGE"
                                                                           nil)
                                                                          (asset
                                                                           "XLV"
                                                                           nil)
                                                                          (asset
                                                                           "XLU"
                                                                           nil)])])])]
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "TQQQ"
                                                                       nil)
                                                                      (filter
                                                                       (rsi
                                                                        {:window
                                                                         10})
                                                                       (select-bottom
                                                                        2)
                                                                       [(asset
                                                                         "TQQQ"
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
                                                                       (rsi
                                                                        {:window
                                                                         10})
                                                                       (select-bottom
                                                                        1)
                                                                       [(asset
                                                                         "TQQQ"
                                                                         nil)
                                                                        (asset
                                                                         "TECL"
                                                                         nil)])])])])])])]
                                                           [(weight-equal
                                                             [(group
                                                               "Conflict Check - SPY on Utilities | 20d XLP vs 20d SH"
                                                               [(weight-equal
                                                                 [(if
                                                                   (>
                                                                    (rsi
                                                                     "XLP"
                                                                     {:window
                                                                      20})
                                                                    (rsi
                                                                     "SH"
                                                                     {:window
                                                                      20}))
                                                                   [(group
                                                                     "Safe Sectors or Bonds"
                                                                     [(weight-equal
                                                                       [(filter
                                                                         (rsi
                                                                          {:window
                                                                           10})
                                                                         (select-bottom
                                                                          1)
                                                                         [(asset
                                                                           "BSV"
                                                                           nil)
                                                                          (asset
                                                                           "TLT"
                                                                           nil)
                                                                          (asset
                                                                           "LQD"
                                                                           nil)
                                                                          (asset
                                                                           "VBF"
                                                                           nil)
                                                                          (asset
                                                                           "XLP"
                                                                           nil)
                                                                          (asset
                                                                           "UGE"
                                                                           nil)
                                                                          (asset
                                                                           "XLV"
                                                                           nil)
                                                                          (asset
                                                                           "XLU"
                                                                           nil)])])])]
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "SQQQ"
                                                                       nil)
                                                                      (filter
                                                                       (moving-average-return
                                                                        {:window
                                                                         15})
                                                                       (select-bottom
                                                                        2)
                                                                       [(asset
                                                                         "SQQQ"
                                                                         nil)
                                                                        (asset
                                                                         "SQQQ"
                                                                         nil)
                                                                        (asset
                                                                         "TECS"
                                                                         nil)
                                                                        (asset
                                                                         "SOXS"
                                                                         nil)])])])])])
                                                              (group
                                                               "Conflict Check - SPY on Bonds | 20d AGG vs 60d SH"
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
                                                                        (current-price
                                                                         "SPY")
                                                                        (moving-average-price
                                                                         "SPY"
                                                                         {:window
                                                                          30}))
                                                                       [(group
                                                                         "Safe Sectors or Bonds"
                                                                         [(weight-equal
                                                                           [(filter
                                                                             (rsi
                                                                              {:window
                                                                               10})
                                                                             (select-bottom
                                                                              1)
                                                                             [(asset
                                                                               "BSV"
                                                                               nil)
                                                                              (asset
                                                                               "TLT"
                                                                               nil)
                                                                              (asset
                                                                               "LQD"
                                                                               nil)
                                                                              (asset
                                                                               "VBF"
                                                                               nil)
                                                                              (asset
                                                                               "XLP"
                                                                               nil)
                                                                              (asset
                                                                               "UGE"
                                                                               nil)
                                                                              (asset
                                                                               "XLV"
                                                                               nil)
                                                                              (asset
                                                                               "XLU"
                                                                               nil)])])])]
                                                                       [(weight-equal
                                                                         [(asset
                                                                           "SQQQ"
                                                                           nil)
                                                                          (filter
                                                                           (moving-average-return
                                                                            {:window
                                                                             15})
                                                                           (select-bottom
                                                                            2)
                                                                           [(asset
                                                                             "SQQQ"
                                                                             nil)
                                                                            (asset
                                                                             "SQQQ"
                                                                             nil)
                                                                            (asset
                                                                             "TECS"
                                                                             nil)
                                                                            (asset
                                                                             "SOXS"
                                                                             nil)])])])])]
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "SQQQ"
                                                                       nil)
                                                                      (filter
                                                                       (moving-average-return
                                                                        {:window
                                                                         15})
                                                                       (select-bottom
                                                                        2)
                                                                       [(asset
                                                                         "SQQQ"
                                                                         nil)
                                                                        (asset
                                                                         "SQQQ"
                                                                         nil)
                                                                        (asset
                                                                         "TECS"
                                                                         nil)
                                                                        (asset
                                                                         "SOXS"
                                                                         nil)])])])])])])])])]))])])]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 3})
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(group
                                                      "Bear Cross"
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           2)
                                                          [(asset
                                                            "SQQQ"
                                                            nil)
                                                           (asset
                                                            "TECS"
                                                            nil)
                                                           (asset
                                                            "SPXU"
                                                            nil)
                                                           (asset
                                                            "TMF"
                                                            nil)
                                                           (asset
                                                            "TMV"
                                                            nil)])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(group
                                                          "QQQ 20d SMA Block"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (current-price
                                                                "QQQ")
                                                               (moving-average-price
                                                                "QQQ"
                                                                {:window
                                                                 20}))
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
                                                                    [(group
                                                                      "Safe Sectors or Bonds"
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (rsi
                                                                           {:window
                                                                            10})
                                                                          (select-bottom
                                                                           1)
                                                                          [(asset
                                                                            "BSV"
                                                                            nil)
                                                                           (asset
                                                                            "TLT"
                                                                            nil)
                                                                           (asset
                                                                            "LQD"
                                                                            nil)
                                                                           (asset
                                                                            "VBF"
                                                                            nil)
                                                                           (asset
                                                                            "XLP"
                                                                            nil)
                                                                           (asset
                                                                            "UGE"
                                                                            nil)
                                                                           (asset
                                                                            "XLV"
                                                                            nil)
                                                                           (asset
                                                                            "XLU"
                                                                            nil)])])])])])])
                                                               (group
                                                                "10d IEF vs 20d PSQ"
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (rsi
                                                                      "PSQ"
                                                                      {:window
                                                                       10})
                                                                     32.5)
                                                                    [(asset
                                                                      "SQQQ"
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
                                                                          "TQQQ"
                                                                          nil)]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (cumulative-return
                                                                              "TQQQ"
                                                                              {:window
                                                                               10})
                                                                             15)
                                                                            [(asset
                                                                              "SQQQ"
                                                                              nil)]
                                                                            [(group
                                                                              "Safe Sectors or Bonds"
                                                                              [(weight-equal
                                                                                [(filter
                                                                                  (rsi
                                                                                   {:window
                                                                                    10})
                                                                                  (select-bottom
                                                                                   1)
                                                                                  [(asset
                                                                                    "BSV"
                                                                                    nil)
                                                                                   (asset
                                                                                    "TLT"
                                                                                    nil)
                                                                                   (asset
                                                                                    "LQD"
                                                                                    nil)
                                                                                   (asset
                                                                                    "VBF"
                                                                                    nil)
                                                                                   (asset
                                                                                    "XLP"
                                                                                    nil)
                                                                                   (asset
                                                                                    "UGE"
                                                                                    nil)
                                                                                   (asset
                                                                                    "XLV"
                                                                                    nil)
                                                                                   (asset
                                                                                    "XLU"
                                                                                    nil)])])])])])])])])])])]
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
                                                                    "Safe Sectors or Bonds"
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (rsi
                                                                         {:window
                                                                          10})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "BSV"
                                                                          nil)
                                                                         (asset
                                                                          "TLT"
                                                                          nil)
                                                                         (asset
                                                                          "LQD"
                                                                          nil)
                                                                         (asset
                                                                          "VBF"
                                                                          nil)
                                                                         (asset
                                                                          "XLP"
                                                                          nil)
                                                                         (asset
                                                                          "UGE"
                                                                          nil)
                                                                         (asset
                                                                          "XLV"
                                                                          nil)
                                                                         (asset
                                                                          "XLU"
                                                                          nil)])])])]
                                                                  [(asset
                                                                    "SQQQ"
                                                                    nil)])
                                                                 (filter
                                                                  (rsi
                                                                   {:window
                                                                    10})
                                                                  (select-top
                                                                   1)
                                                                  [(asset
                                                                    "SQQQ"
                                                                    nil)
                                                                   (asset
                                                                    "TLT"
                                                                    nil)])])])])])
                                                         (group
                                                          "TQQQ 20d SMA Block"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (current-price
                                                                "TQQQ")
                                                               (moving-average-price
                                                                "TQQQ"
                                                                {:window
                                                                 20}))
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
                                                                    [(group
                                                                      "Safe Sectors or Bonds"
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (rsi
                                                                           {:window
                                                                            10})
                                                                          (select-bottom
                                                                           1)
                                                                          [(asset
                                                                            "BSV"
                                                                            nil)
                                                                           (asset
                                                                            "TLT"
                                                                            nil)
                                                                           (asset
                                                                            "LQD"
                                                                            nil)
                                                                           (asset
                                                                            "VBF"
                                                                            nil)
                                                                           (asset
                                                                            "XLP"
                                                                            nil)
                                                                           (asset
                                                                            "UGE"
                                                                            nil)
                                                                           (asset
                                                                            "XLV"
                                                                            nil)
                                                                           (asset
                                                                            "XLU"
                                                                            nil)])])])])])])
                                                               (group
                                                                "10d IEF vs 20d PSQ"
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (rsi
                                                                      "PSQ"
                                                                      {:window
                                                                       10})
                                                                     32.5)
                                                                    [(asset
                                                                      "SQQQ"
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
                                                                          "TQQQ"
                                                                          nil)]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (cumulative-return
                                                                              "TQQQ"
                                                                              {:window
                                                                               10})
                                                                             15)
                                                                            [(asset
                                                                              "SQQQ"
                                                                              nil)]
                                                                            [(group
                                                                              "Safe Sectors or Bonds"
                                                                              [(weight-equal
                                                                                [(filter
                                                                                  (rsi
                                                                                   {:window
                                                                                    10})
                                                                                  (select-bottom
                                                                                   1)
                                                                                  [(asset
                                                                                    "BSV"
                                                                                    nil)
                                                                                   (asset
                                                                                    "TLT"
                                                                                    nil)
                                                                                   (asset
                                                                                    "LQD"
                                                                                    nil)
                                                                                   (asset
                                                                                    "VBF"
                                                                                    nil)
                                                                                   (asset
                                                                                    "XLP"
                                                                                    nil)
                                                                                   (asset
                                                                                    "UGE"
                                                                                    nil)
                                                                                   (asset
                                                                                    "XLV"
                                                                                    nil)
                                                                                   (asset
                                                                                    "XLU"
                                                                                    nil)])])])])])])])])])])]
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
                                                                    "Safe Sectors or Bonds"
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (rsi
                                                                         {:window
                                                                          10})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "BSV"
                                                                          nil)
                                                                         (asset
                                                                          "TLT"
                                                                          nil)
                                                                         (asset
                                                                          "LQD"
                                                                          nil)
                                                                         (asset
                                                                          "VBF"
                                                                          nil)
                                                                         (asset
                                                                          "XLP"
                                                                          nil)
                                                                         (asset
                                                                          "UGE"
                                                                          nil)
                                                                         (asset
                                                                          "XLV"
                                                                          nil)
                                                                         (asset
                                                                          "XLU"
                                                                          nil)])])])]
                                                                  [(asset
                                                                    "SQQQ"
                                                                    nil)])
                                                                 (filter
                                                                  (rsi
                                                                   {:window
                                                                    10})
                                                                  (select-top
                                                                   1)
                                                                  [(asset
                                                                    "SQQQ"
                                                                    nil)
                                                                   (asset
                                                                    "TLT"
                                                                    nil)])])])])])]
                                                        [(group
                                                          "15d AGG vs TQQQ"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (rsi
                                                                "AGG"
                                                                {:window
                                                                 15})
                                                               (rsi
                                                                "TQQQ"
                                                                {:window
                                                                 15}))
                                                              [(weight-equal
                                                                [(asset
                                                                  "TQQQ"
                                                                  nil)
                                                                 (filter
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
                                                                    "TQQQ"
                                                                    nil)
                                                                   (asset
                                                                    "TECL"
                                                                    nil)
                                                                   (asset
                                                                    "SOXL"
                                                                    nil)])])]
                                                              [(weight-equal
                                                                [(group
                                                                  "Safe Sectors or Bonds"
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (rsi
                                                                       {:window
                                                                        10})
                                                                      (select-bottom
                                                                       1)
                                                                      [(asset
                                                                        "BSV"
                                                                        nil)
                                                                       (asset
                                                                        "TLT"
                                                                        nil)
                                                                       (asset
                                                                        "LQD"
                                                                        nil)
                                                                       (asset
                                                                        "VBF"
                                                                        nil)
                                                                       (asset
                                                                        "XLP"
                                                                        nil)
                                                                       (asset
                                                                        "UGE"
                                                                        nil)
                                                                       (asset
                                                                        "XLV"
                                                                        nil)
                                                                       (asset
                                                                        "XLU"
                                                                        nil)])])])
                                                                 (filter
                                                                  (rsi
                                                                   {:window
                                                                    10})
                                                                  (select-top
                                                                   1)
                                                                  [(asset
                                                                    "SQQQ"
                                                                    nil)
                                                                   (asset
                                                                    "TLT"
                                                                    nil)])])])])])
                                                         (group
                                                          "15d AGG vs QQQ"
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
                                                              [(weight-equal
                                                                [(asset
                                                                  "TQQQ"
                                                                  nil)
                                                                 (filter
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
                                                                    "TQQQ"
                                                                    nil)
                                                                   (asset
                                                                    "TECL"
                                                                    nil)
                                                                   (asset
                                                                    "SOXL"
                                                                    nil)])])]
                                                              [(weight-equal
                                                                [(group
                                                                  "Safe Sectors or Bonds"
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (rsi
                                                                       {:window
                                                                        10})
                                                                      (select-bottom
                                                                       1)
                                                                      [(asset
                                                                        "BSV"
                                                                        nil)
                                                                       (asset
                                                                        "TLT"
                                                                        nil)
                                                                       (asset
                                                                        "LQD"
                                                                        nil)
                                                                       (asset
                                                                        "VBF"
                                                                        nil)
                                                                       (asset
                                                                        "XLP"
                                                                        nil)
                                                                       (asset
                                                                        "UGE"
                                                                        nil)
                                                                       (asset
                                                                        "XLV"
                                                                        nil)
                                                                       (asset
                                                                        "XLU"
                                                                        nil)])])])
                                                                 (filter
                                                                  (rsi
                                                                   {:window
                                                                    10})
                                                                  (select-top
                                                                   1)
                                                                  [(asset
                                                                    "SQQQ"
                                                                    nil)
                                                                   (asset
                                                                    "TLT"
                                                                    nil)])])])])])])])])])])])])
                                           (group
                                            "TQQQ 200 DMA"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (current-price "TQQQ")
                                                 (moving-average-price
                                                  "TQQQ"
                                                  {:window 200}))
                                                [(weight-equal
                                                  [(if
                                                    (<
                                                     (moving-average-price
                                                      "TQQQ"
                                                      {:window 3})
                                                     (moving-average-price
                                                      "TQQQ"
                                                      {:window 200}))
                                                    [(group
                                                      "Bull Cross "
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           2)
                                                          [(asset
                                                            "TQQQ"
                                                            nil)
                                                           (asset
                                                            "TECL"
                                                            nil)
                                                           (asset
                                                            "SPXL"
                                                            nil)
                                                           (asset
                                                            "TMF"
                                                            nil)])])])]
                                                    [(weight-specified
                                                      0.2
                                                      (group
                                                       "SPY on Bonds | 20d AGG vs 60d SH"
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
                                                                (current-price
                                                                 "SPY")
                                                                (moving-average-price
                                                                 "SPY"
                                                                 {:window
                                                                  30}))
                                                               [(group
                                                                 "Conflict Check - KMLM Fund Surfing"
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
                                                                       [(asset
                                                                         "TQQQ"
                                                                         nil)
                                                                        (filter
                                                                         (moving-average-return
                                                                          {:window
                                                                           15})
                                                                         (select-top
                                                                          2)
                                                                         [(asset
                                                                           "TQQQ"
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
                                                                           15})
                                                                         (select-top
                                                                          1)
                                                                         [(asset
                                                                           "TQQQ"
                                                                           nil)
                                                                          (asset
                                                                           "TECL"
                                                                           nil)])])]
                                                                     [(group
                                                                       "Safe Sectors or Bonds"
                                                                       [(weight-equal
                                                                         [(filter
                                                                           (rsi
                                                                            {:window
                                                                             10})
                                                                           (select-bottom
                                                                            1)
                                                                           [(asset
                                                                             "BSV"
                                                                             nil)
                                                                            (asset
                                                                             "TLT"
                                                                             nil)
                                                                            (asset
                                                                             "LQD"
                                                                             nil)
                                                                            (asset
                                                                             "VBF"
                                                                             nil)
                                                                            (asset
                                                                             "XLP"
                                                                             nil)
                                                                            (asset
                                                                             "UGE"
                                                                             nil)
                                                                            (asset
                                                                             "XLV"
                                                                             nil)
                                                                            (asset
                                                                             "XLU"
                                                                             nil)])])])])])])]
                                                               [(group
                                                                 "Safe Sectors or Bonds"
                                                                 [(weight-equal
                                                                   [(filter
                                                                     (rsi
                                                                      {:window
                                                                       10})
                                                                     (select-bottom
                                                                      1)
                                                                     [(asset
                                                                       "BSV"
                                                                       nil)
                                                                      (asset
                                                                       "TLT"
                                                                       nil)
                                                                      (asset
                                                                       "LQD"
                                                                       nil)
                                                                      (asset
                                                                       "VBF"
                                                                       nil)
                                                                      (asset
                                                                       "XLP"
                                                                       nil)
                                                                      (asset
                                                                       "UGE"
                                                                       nil)
                                                                      (asset
                                                                       "XLV"
                                                                       nil)
                                                                      (asset
                                                                       "XLU"
                                                                       nil)])])])])])]
                                                           [(group
                                                             "Safe Sectors or Bonds"
                                                             [(weight-equal
                                                               [(filter
                                                                 (rsi
                                                                  {:window
                                                                   10})
                                                                 (select-bottom
                                                                  1)
                                                                 [(asset
                                                                   "BSV"
                                                                   nil)
                                                                  (asset
                                                                   "TLT"
                                                                   nil)
                                                                  (asset
                                                                   "LQD"
                                                                   nil)
                                                                  (asset
                                                                   "VBF"
                                                                   nil)
                                                                  (asset
                                                                   "XLP"
                                                                   nil)
                                                                  (asset
                                                                   "UGE"
                                                                   nil)
                                                                  (asset
                                                                   "XLV"
                                                                   nil)
                                                                  (asset
                                                                   "XLU"
                                                                   nil)])])])])])])
                                                      0.2
                                                      (group
                                                       "SPY on Staples | 20d XLP vs 20d SH"
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (rsi
                                                             "XLP"
                                                             {:window
                                                              20})
                                                            (rsi
                                                             "SH"
                                                             {:window
                                                              20}))
                                                           [(group
                                                             "Conflict Check - KMLM Fund Surfing"
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
                                                                   [(asset
                                                                     "TQQQ"
                                                                     nil)
                                                                    (filter
                                                                     (rsi
                                                                      {:window
                                                                       10})
                                                                     (select-bottom
                                                                      2)
                                                                     [(asset
                                                                       "TQQQ"
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
                                                                     (rsi
                                                                      {:window
                                                                       10})
                                                                     (select-bottom
                                                                      1)
                                                                     [(asset
                                                                       "TQQQ"
                                                                       nil)
                                                                      (asset
                                                                       "TECL"
                                                                       nil)])])]
                                                                 [(group
                                                                   "Safe Sectors or Bonds"
                                                                   [(weight-equal
                                                                     [(filter
                                                                       (rsi
                                                                        {:window
                                                                         10})
                                                                       (select-bottom
                                                                        1)
                                                                       [(asset
                                                                         "BSV"
                                                                         nil)
                                                                        (asset
                                                                         "TLT"
                                                                         nil)
                                                                        (asset
                                                                         "LQD"
                                                                         nil)
                                                                        (asset
                                                                         "VBF"
                                                                         nil)
                                                                        (asset
                                                                         "XLP"
                                                                         nil)
                                                                        (asset
                                                                         "UGE"
                                                                         nil)
                                                                        (asset
                                                                         "XLV"
                                                                         nil)
                                                                        (asset
                                                                         "XLU"
                                                                         nil)])])])])])])]
                                                           [(group
                                                             "Safe Sectors or Bonds"
                                                             [(weight-equal
                                                               [(filter
                                                                 (rsi
                                                                  {:window
                                                                   10})
                                                                 (select-bottom
                                                                  1)
                                                                 [(asset
                                                                   "BSV"
                                                                   nil)
                                                                  (asset
                                                                   "TLT"
                                                                   nil)
                                                                  (asset
                                                                   "LQD"
                                                                   nil)
                                                                  (asset
                                                                   "VBF"
                                                                   nil)
                                                                  (asset
                                                                   "XLP"
                                                                   nil)
                                                                  (asset
                                                                   "UGE"
                                                                   nil)
                                                                  (asset
                                                                   "XLV"
                                                                   nil)
                                                                  (asset
                                                                   "XLU"
                                                                   nil)])])])])])])
                                                      0.2
                                                      (group
                                                       "A Better \"Buy the Dips Nasdaq\" by Garen Phillips | Safe Sectors Mod"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "QQQ"
                                                             {:window
                                                              5})
                                                            -6)
                                                           [(group
                                                             "Conflict Check: KMLM Fund Surfing"
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
                                                                   "Safe Sectors or Bonds"
                                                                   [(weight-equal
                                                                     [(filter
                                                                       (rsi
                                                                        {:window
                                                                         10})
                                                                       (select-bottom
                                                                        1)
                                                                       [(asset
                                                                         "BSV"
                                                                         nil)
                                                                        (asset
                                                                         "TLT"
                                                                         nil)
                                                                        (asset
                                                                         "LQD"
                                                                         nil)
                                                                        (asset
                                                                         "VBF"
                                                                         nil)
                                                                        (asset
                                                                         "XLP"
                                                                         nil)
                                                                        (asset
                                                                         "UGE"
                                                                         nil)
                                                                        (asset
                                                                         "XLV"
                                                                         nil)
                                                                        (asset
                                                                         "XLU"
                                                                         nil)])])])]
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "SQQQ"
                                                                     nil)
                                                                    (filter
                                                                     (moving-average-return
                                                                      {:window
                                                                       15})
                                                                     (select-bottom
                                                                      2)
                                                                     [(asset
                                                                       "SQQQ"
                                                                       nil)
                                                                      (asset
                                                                       "SQQQ"
                                                                       nil)
                                                                      (asset
                                                                       "TECS"
                                                                       nil)
                                                                      (asset
                                                                       "SOXS"
                                                                       nil)])])])])])]
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (stdev-return
                                                                 "TQQQ"
                                                                 {:window
                                                                  10})
                                                                5)
                                                               [(group
                                                                 "Safe Sectors or Bonds"
                                                                 [(weight-equal
                                                                   [(filter
                                                                     (rsi
                                                                      {:window
                                                                       10})
                                                                     (select-bottom
                                                                      1)
                                                                     [(asset
                                                                       "BSV"
                                                                       nil)
                                                                      (asset
                                                                       "TLT"
                                                                       nil)
                                                                      (asset
                                                                       "LQD"
                                                                       nil)
                                                                      (asset
                                                                       "VBF"
                                                                       nil)
                                                                      (asset
                                                                       "XLP"
                                                                       nil)
                                                                      (asset
                                                                       "UGE"
                                                                       nil)
                                                                      (asset
                                                                       "XLV"
                                                                       nil)
                                                                      (asset
                                                                       "XLU"
                                                                       nil)])])])]
                                                               [(weight-equal
                                                                 [(asset
                                                                   "TQQQ"
                                                                   nil)
                                                                  (filter
                                                                   (moving-average-return
                                                                    {:window
                                                                     10})
                                                                   (select-top
                                                                    2)
                                                                   [(asset
                                                                     "TQQQ"
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
                                                                   (select-top
                                                                    1)
                                                                   [(asset
                                                                     "TQQQ"
                                                                     nil)
                                                                    (asset
                                                                     "TECL"
                                                                     nil)])])])])])])])
                                                      0.4
                                                      (group
                                                       "KMLM Fund Surfing"
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
                                                             [(weight-equal
                                                               [(asset
                                                                 "TQQQ"
                                                                 nil)
                                                                (filter
                                                                 (rsi
                                                                  {:window
                                                                   10})
                                                                 (select-bottom
                                                                  2)
                                                                 [(asset
                                                                   "TQQQ"
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
                                                                 (rsi
                                                                  {:window
                                                                   10})
                                                                 (select-bottom
                                                                  1)
                                                                 [(asset
                                                                   "TQQQ"
                                                                   nil)
                                                                  (asset
                                                                   "TECL"
                                                                   nil)])])
                                                              (group
                                                               "Conflict Check - A Better \"Buy the Dips Nasdaq\" by Garen Phillips | Safe Sectors Mod"
                                                               [(weight-equal
                                                                 [(if
                                                                   (<
                                                                    (cumulative-return
                                                                     "QQQ"
                                                                     {:window
                                                                      5})
                                                                    -6)
                                                                   [(group
                                                                     "Safe Sectors or Bonds"
                                                                     [(weight-equal
                                                                       [(filter
                                                                         (rsi
                                                                          {:window
                                                                           10})
                                                                         (select-bottom
                                                                          1)
                                                                         [(asset
                                                                           "BSV"
                                                                           nil)
                                                                          (asset
                                                                           "TLT"
                                                                           nil)
                                                                          (asset
                                                                           "LQD"
                                                                           nil)
                                                                          (asset
                                                                           "VBF"
                                                                           nil)
                                                                          (asset
                                                                           "XLP"
                                                                           nil)
                                                                          (asset
                                                                           "UGE"
                                                                           nil)
                                                                          (asset
                                                                           "XLV"
                                                                           nil)
                                                                          (asset
                                                                           "XLU"
                                                                           nil)])])])]
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "TQQQ"
                                                                       nil)
                                                                      (filter
                                                                       (rsi
                                                                        {:window
                                                                         10})
                                                                       (select-bottom
                                                                        2)
                                                                       [(asset
                                                                         "TQQQ"
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
                                                                       (rsi
                                                                        {:window
                                                                         10})
                                                                       (select-bottom
                                                                        1)
                                                                       [(asset
                                                                         "TQQQ"
                                                                         nil)
                                                                        (asset
                                                                         "TECL"
                                                                         nil)])])])])])])]
                                                           [(weight-equal
                                                             [(group
                                                               "Conflict Check - SPY on Utilities | 20d XLP vs 20d SH"
                                                               [(weight-equal
                                                                 [(if
                                                                   (>
                                                                    (rsi
                                                                     "XLP"
                                                                     {:window
                                                                      20})
                                                                    (rsi
                                                                     "SH"
                                                                     {:window
                                                                      20}))
                                                                   [(group
                                                                     "Safe Sectors or Bonds"
                                                                     [(weight-equal
                                                                       [(filter
                                                                         (rsi
                                                                          {:window
                                                                           10})
                                                                         (select-bottom
                                                                          1)
                                                                         [(asset
                                                                           "BSV"
                                                                           nil)
                                                                          (asset
                                                                           "TLT"
                                                                           nil)
                                                                          (asset
                                                                           "LQD"
                                                                           nil)
                                                                          (asset
                                                                           "VBF"
                                                                           nil)
                                                                          (asset
                                                                           "XLP"
                                                                           nil)
                                                                          (asset
                                                                           "UGE"
                                                                           nil)
                                                                          (asset
                                                                           "XLV"
                                                                           nil)
                                                                          (asset
                                                                           "XLU"
                                                                           nil)])])])]
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "SQQQ"
                                                                       nil)
                                                                      (filter
                                                                       (moving-average-return
                                                                        {:window
                                                                         15})
                                                                       (select-bottom
                                                                        2)
                                                                       [(asset
                                                                         "SQQQ"
                                                                         nil)
                                                                        (asset
                                                                         "SQQQ"
                                                                         nil)
                                                                        (asset
                                                                         "TECS"
                                                                         nil)
                                                                        (asset
                                                                         "SOXS"
                                                                         nil)])])])])])
                                                              (group
                                                               "Conflict Check - SPY on Bonds | 20d AGG vs 60d SH"
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
                                                                        (current-price
                                                                         "SPY")
                                                                        (moving-average-price
                                                                         "SPY"
                                                                         {:window
                                                                          30}))
                                                                       [(group
                                                                         "Safe Sectors or Bonds"
                                                                         [(weight-equal
                                                                           [(filter
                                                                             (rsi
                                                                              {:window
                                                                               10})
                                                                             (select-bottom
                                                                              1)
                                                                             [(asset
                                                                               "BSV"
                                                                               nil)
                                                                              (asset
                                                                               "TLT"
                                                                               nil)
                                                                              (asset
                                                                               "LQD"
                                                                               nil)
                                                                              (asset
                                                                               "VBF"
                                                                               nil)
                                                                              (asset
                                                                               "XLP"
                                                                               nil)
                                                                              (asset
                                                                               "UGE"
                                                                               nil)
                                                                              (asset
                                                                               "XLV"
                                                                               nil)
                                                                              (asset
                                                                               "XLU"
                                                                               nil)])])])]
                                                                       [(weight-equal
                                                                         [(asset
                                                                           "SQQQ"
                                                                           nil)
                                                                          (filter
                                                                           (moving-average-return
                                                                            {:window
                                                                             15})
                                                                           (select-bottom
                                                                            2)
                                                                           [(asset
                                                                             "SQQQ"
                                                                             nil)
                                                                            (asset
                                                                             "SQQQ"
                                                                             nil)
                                                                            (asset
                                                                             "TECS"
                                                                             nil)
                                                                            (asset
                                                                             "SOXS"
                                                                             nil)])])])])]
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "SQQQ"
                                                                       nil)
                                                                      (filter
                                                                       (moving-average-return
                                                                        {:window
                                                                         15})
                                                                       (select-bottom
                                                                        2)
                                                                       [(asset
                                                                         "SQQQ"
                                                                         nil)
                                                                        (asset
                                                                         "SQQQ"
                                                                         nil)
                                                                        (asset
                                                                         "TECS"
                                                                         nil)
                                                                        (asset
                                                                         "SOXS"
                                                                         nil)])])])])])])])])]))])])]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "QQQ"
                                                      {:window 60})
                                                     -12)
                                                    [(group
                                                      "QQQ 20d SMA Block"
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (current-price
                                                            "QQQ")
                                                           (moving-average-price
                                                            "QQQ"
                                                            {:window
                                                             20}))
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
                                                                [(group
                                                                  "Safe Sectors or Bonds"
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (rsi
                                                                       {:window
                                                                        10})
                                                                      (select-bottom
                                                                       1)
                                                                      [(asset
                                                                        "BSV"
                                                                        nil)
                                                                       (asset
                                                                        "TLT"
                                                                        nil)
                                                                       (asset
                                                                        "LQD"
                                                                        nil)
                                                                       (asset
                                                                        "VBF"
                                                                        nil)
                                                                       (asset
                                                                        "XLP"
                                                                        nil)
                                                                       (asset
                                                                        "UGE"
                                                                        nil)
                                                                       (asset
                                                                        "XLV"
                                                                        nil)
                                                                       (asset
                                                                        "XLU"
                                                                        nil)])])])])])])
                                                           (group
                                                            "10d IEF vs 20d PSQ"
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (rsi
                                                                  "PSQ"
                                                                  {:window
                                                                   10})
                                                                 32.5)
                                                                [(asset
                                                                  "SQQQ"
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
                                                                      "TQQQ"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (cumulative-return
                                                                          "TQQQ"
                                                                          {:window
                                                                           10})
                                                                         15)
                                                                        [(asset
                                                                          "SQQQ"
                                                                          nil)]
                                                                        [(group
                                                                          "Safe Sectors or Bonds"
                                                                          [(weight-equal
                                                                            [(filter
                                                                              (rsi
                                                                               {:window
                                                                                10})
                                                                              (select-bottom
                                                                               1)
                                                                              [(asset
                                                                                "BSV"
                                                                                nil)
                                                                               (asset
                                                                                "TLT"
                                                                                nil)
                                                                               (asset
                                                                                "LQD"
                                                                                nil)
                                                                               (asset
                                                                                "VBF"
                                                                                nil)
                                                                               (asset
                                                                                "XLP"
                                                                                nil)
                                                                               (asset
                                                                                "UGE"
                                                                                nil)
                                                                               (asset
                                                                                "XLV"
                                                                                nil)
                                                                               (asset
                                                                                "XLU"
                                                                                nil)])])])])])])])])])])]
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
                                                                "Safe Sectors or Bonds"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (rsi
                                                                     {:window
                                                                      10})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "BSV"
                                                                      nil)
                                                                     (asset
                                                                      "TLT"
                                                                      nil)
                                                                     (asset
                                                                      "LQD"
                                                                      nil)
                                                                     (asset
                                                                      "VBF"
                                                                      nil)
                                                                     (asset
                                                                      "XLP"
                                                                      nil)
                                                                     (asset
                                                                      "UGE"
                                                                      nil)
                                                                     (asset
                                                                      "XLV"
                                                                      nil)
                                                                     (asset
                                                                      "XLU"
                                                                      nil)])])])]
                                                              [(asset
                                                                "SQQQ"
                                                                nil)])
                                                             (filter
                                                              (rsi
                                                               {:window
                                                                10})
                                                              (select-top
                                                               1)
                                                              [(asset
                                                                "SQQQ"
                                                                nil)
                                                               (asset
                                                                "TLT"
                                                                nil)])])])])])
                                                     (group
                                                      "TQQQ 20d SMA Block"
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (current-price
                                                            "TQQQ")
                                                           (moving-average-price
                                                            "TQQQ"
                                                            {:window
                                                             20}))
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
                                                                [(group
                                                                  "Safe Sectors or Bonds"
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (rsi
                                                                       {:window
                                                                        10})
                                                                      (select-bottom
                                                                       1)
                                                                      [(asset
                                                                        "BSV"
                                                                        nil)
                                                                       (asset
                                                                        "TLT"
                                                                        nil)
                                                                       (asset
                                                                        "LQD"
                                                                        nil)
                                                                       (asset
                                                                        "VBF"
                                                                        nil)
                                                                       (asset
                                                                        "XLP"
                                                                        nil)
                                                                       (asset
                                                                        "UGE"
                                                                        nil)
                                                                       (asset
                                                                        "XLV"
                                                                        nil)
                                                                       (asset
                                                                        "XLU"
                                                                        nil)])])])])])])
                                                           (group
                                                            "10d IEF vs 20d PSQ"
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (rsi
                                                                  "PSQ"
                                                                  {:window
                                                                   10})
                                                                 32.5)
                                                                [(asset
                                                                  "SQQQ"
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
                                                                      "TQQQ"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (cumulative-return
                                                                          "TQQQ"
                                                                          {:window
                                                                           10})
                                                                         15)
                                                                        [(asset
                                                                          "SQQQ"
                                                                          nil)]
                                                                        [(group
                                                                          "Safe Sectors or Bonds"
                                                                          [(weight-equal
                                                                            [(filter
                                                                              (rsi
                                                                               {:window
                                                                                10})
                                                                              (select-bottom
                                                                               1)
                                                                              [(asset
                                                                                "BSV"
                                                                                nil)
                                                                               (asset
                                                                                "TLT"
                                                                                nil)
                                                                               (asset
                                                                                "LQD"
                                                                                nil)
                                                                               (asset
                                                                                "VBF"
                                                                                nil)
                                                                               (asset
                                                                                "XLP"
                                                                                nil)
                                                                               (asset
                                                                                "UGE"
                                                                                nil)
                                                                               (asset
                                                                                "XLV"
                                                                                nil)
                                                                               (asset
                                                                                "XLU"
                                                                                nil)])])])])])])])])])])]
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
                                                                "Safe Sectors or Bonds"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (rsi
                                                                     {:window
                                                                      10})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "BSV"
                                                                      nil)
                                                                     (asset
                                                                      "TLT"
                                                                      nil)
                                                                     (asset
                                                                      "LQD"
                                                                      nil)
                                                                     (asset
                                                                      "VBF"
                                                                      nil)
                                                                     (asset
                                                                      "XLP"
                                                                      nil)
                                                                     (asset
                                                                      "UGE"
                                                                      nil)
                                                                     (asset
                                                                      "XLV"
                                                                      nil)
                                                                     (asset
                                                                      "XLU"
                                                                      nil)])])])]
                                                              [(asset
                                                                "SQQQ"
                                                                nil)])
                                                             (filter
                                                              (rsi
                                                               {:window
                                                                10})
                                                              (select-top
                                                               1)
                                                              [(asset
                                                                "SQQQ"
                                                                nil)
                                                               (asset
                                                                "TLT"
                                                                nil)])])])])])]
                                                    [(group
                                                      "15d AGG vs TQQQ"
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (rsi
                                                            "AGG"
                                                            {:window
                                                             15})
                                                           (rsi
                                                            "TQQQ"
                                                            {:window
                                                             15}))
                                                          [(weight-equal
                                                            [(asset
                                                              "TQQQ"
                                                              nil)
                                                             (filter
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
                                                                "TQQQ"
                                                                nil)
                                                               (asset
                                                                "TECL"
                                                                nil)
                                                               (asset
                                                                "SOXL"
                                                                nil)])])]
                                                          [(weight-equal
                                                            [(group
                                                              "Safe Sectors or Bonds"
                                                              [(weight-equal
                                                                [(filter
                                                                  (rsi
                                                                   {:window
                                                                    10})
                                                                  (select-bottom
                                                                   1)
                                                                  [(asset
                                                                    "BSV"
                                                                    nil)
                                                                   (asset
                                                                    "TLT"
                                                                    nil)
                                                                   (asset
                                                                    "LQD"
                                                                    nil)
                                                                   (asset
                                                                    "VBF"
                                                                    nil)
                                                                   (asset
                                                                    "XLP"
                                                                    nil)
                                                                   (asset
                                                                    "UGE"
                                                                    nil)
                                                                   (asset
                                                                    "XLV"
                                                                    nil)
                                                                   (asset
                                                                    "XLU"
                                                                    nil)])])])
                                                             (filter
                                                              (rsi
                                                               {:window
                                                                10})
                                                              (select-top
                                                               1)
                                                              [(asset
                                                                "SQQQ"
                                                                nil)
                                                               (asset
                                                                "TLT"
                                                                nil)])])])])])
                                                     (group
                                                      "15d AGG vs QQQ"
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
                                                          [(weight-equal
                                                            [(asset
                                                              "TQQQ"
                                                              nil)
                                                             (filter
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
                                                                "TQQQ"
                                                                nil)
                                                               (asset
                                                                "TECL"
                                                                nil)
                                                               (asset
                                                                "SOXL"
                                                                nil)])])]
                                                          [(weight-equal
                                                            [(group
                                                              "Safe Sectors or Bonds"
                                                              [(weight-equal
                                                                [(filter
                                                                  (rsi
                                                                   {:window
                                                                    10})
                                                                  (select-bottom
                                                                   1)
                                                                  [(asset
                                                                    "BSV"
                                                                    nil)
                                                                   (asset
                                                                    "TLT"
                                                                    nil)
                                                                   (asset
                                                                    "LQD"
                                                                    nil)
                                                                   (asset
                                                                    "VBF"
                                                                    nil)
                                                                   (asset
                                                                    "XLP"
                                                                    nil)
                                                                   (asset
                                                                    "UGE"
                                                                    nil)
                                                                   (asset
                                                                    "XLV"
                                                                    nil)
                                                                   (asset
                                                                    "XLU"
                                                                    nil)])])])
                                                             (filter
                                                              (rsi
                                                               {:window
                                                                10})
                                                              (select-top
                                                               1)
                                                              [(asset
                                                                "SQQQ"
                                                                nil)
                                                               (asset
                                                                "TLT"
                                                                nil)])])])])])])])])])])])])])])])])])
                             0.25
                             (group
                              "Rain's Overcompensating Safety Checks for TQQQs (194,35,2011)"
                              [(weight-equal
                                [(group
                                  "Largest Cumulative Return (69,36,2011)"
                                  [(weight-equal
                                    [(filter
                                      (cumulative-return {:window 9})
                                      (select-top 4)
                                      [(group
                                        "Group 1 | 75d CR < 75d MAR"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (cumulative-return
                                              "QQQ"
                                              {:window 75})
                                             (moving-average-return
                                              "QQQ"
                                              {:window 75}))
                                            [(weight-equal
                                              [(group
                                                "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (current-price
                                                          "TQQQ")
                                                         (moving-average-price
                                                          "TQQQ"
                                                          {:window
                                                           20}))
                                                        [(weight-equal
                                                          [(filter
                                                            (rsi
                                                             {:window
                                                              10})
                                                            (select-top
                                                             1)
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
                                                              {:window
                                                               10})
                                                             31)
                                                            [(asset
                                                              "SQQQ"
                                                              "ProShares UltraPro Short QQQ")]
                                                            [(asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")])])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 2 | 3d CR > 10d StDev"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (cumulative-return
                                              "QQQ"
                                              {:window 3})
                                             (stdev-return
                                              "QQQ"
                                              {:window 10}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 3 | 3d MAR > 10d StDev"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (moving-average-return
                                              "QQQ"
                                              {:window 3})
                                             (stdev-return
                                              "QQQ"
                                              {:window 10}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 4 | price > 15d SMA"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (current-price "QQQ")
                                             (moving-average-price
                                              "QQQ"
                                              {:window 15}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 5 | price < 100d SMA"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (current-price "QQQ")
                                             (moving-average-price
                                              "QQQ"
                                              {:window 100}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 6 | price > 50d SMA"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (current-price "QQQ")
                                             (moving-average-price
                                              "QQQ"
                                              {:window 50}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 7 | 20d EMA > 200d SMA"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (exponential-moving-average-price
                                              "QQQ"
                                              {:window 20})
                                             (moving-average-price
                                              "QQQ"
                                              {:window 200}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 8 | 10d RSI > 50d RSI"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "QQQ" {:window 10})
                                             (rsi "QQQ" {:window 50}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 9 | 50d RSI < 55"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (rsi "QQQ" {:window 50})
                                             55)
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 10 | 100d RSI < 60"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (rsi "QQQ" {:window 100})
                                             60)
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])])])])
                                 (group
                                  "Smallest Max Drawdown (65,33,2011)"
                                  [(weight-equal
                                    [(filter
                                      (max-drawdown {:window 50})
                                      (select-bottom 4)
                                      [(group
                                        "Group 1 | 75d CR < 75d MAR"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (cumulative-return
                                              "QQQ"
                                              {:window 75})
                                             (moving-average-return
                                              "QQQ"
                                              {:window 75}))
                                            [(weight-equal
                                              [(group
                                                "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (current-price
                                                          "TQQQ")
                                                         (moving-average-price
                                                          "TQQQ"
                                                          {:window
                                                           20}))
                                                        [(weight-equal
                                                          [(filter
                                                            (rsi
                                                             {:window
                                                              10})
                                                            (select-top
                                                             1)
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
                                                              {:window
                                                               10})
                                                             31)
                                                            [(asset
                                                              "SQQQ"
                                                              "ProShares UltraPro Short QQQ")]
                                                            [(asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")])])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 2 | 3d CR > 10d StDev"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (cumulative-return
                                              "QQQ"
                                              {:window 3})
                                             (stdev-return
                                              "QQQ"
                                              {:window 10}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 3 | 3d MAR > 10d StDev"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (moving-average-return
                                              "QQQ"
                                              {:window 3})
                                             (stdev-return
                                              "QQQ"
                                              {:window 10}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 4 | price > 15d SMA"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (current-price "QQQ")
                                             (moving-average-price
                                              "QQQ"
                                              {:window 15}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 5 | price < 100d SMA"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (current-price "QQQ")
                                             (moving-average-price
                                              "QQQ"
                                              {:window 100}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 6 | price > 50d SMA"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (current-price "QQQ")
                                             (moving-average-price
                                              "QQQ"
                                              {:window 50}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 7 | 20d EMA > 200d SMA"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (exponential-moving-average-price
                                              "QQQ"
                                              {:window 20})
                                             (moving-average-price
                                              "QQQ"
                                              {:window 200}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 8 | 10d RSI > 50d RSI"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "QQQ" {:window 10})
                                             (rsi "QQQ" {:window 50}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 9 | 50d RSI < 55"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (rsi "QQQ" {:window 50})
                                             55)
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 10 | 100d RSI < 60"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (rsi "QQQ" {:window 100})
                                             60)
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])])])])
                                 (group
                                  "Largest Volatility (74,54,2011)"
                                  [(weight-equal
                                    [(filter
                                      (stdev-return {:window 15})
                                      (select-top 4)
                                      [(group
                                        "Group 1 | 75d CR < 75d MAR"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (cumulative-return
                                              "QQQ"
                                              {:window 75})
                                             (moving-average-return
                                              "QQQ"
                                              {:window 75}))
                                            [(weight-equal
                                              [(group
                                                "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (current-price
                                                          "TQQQ")
                                                         (moving-average-price
                                                          "TQQQ"
                                                          {:window
                                                           20}))
                                                        [(weight-equal
                                                          [(filter
                                                            (rsi
                                                             {:window
                                                              10})
                                                            (select-top
                                                             1)
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
                                                              {:window
                                                               10})
                                                             31)
                                                            [(asset
                                                              "SQQQ"
                                                              "ProShares UltraPro Short QQQ")]
                                                            [(asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")])])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 2 | 3d CR > 10d StDev"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (cumulative-return
                                              "QQQ"
                                              {:window 3})
                                             (stdev-return
                                              "QQQ"
                                              {:window 10}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 3 | 3d MAR > 10d StDev"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (moving-average-return
                                              "QQQ"
                                              {:window 3})
                                             (stdev-return
                                              "QQQ"
                                              {:window 10}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 4 | price > 15d SMA"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (current-price "QQQ")
                                             (moving-average-price
                                              "QQQ"
                                              {:window 15}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 5 | price < 100d SMA"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (current-price "QQQ")
                                             (moving-average-price
                                              "QQQ"
                                              {:window 100}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 6 | price > 50d SMA"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (current-price "QQQ")
                                             (moving-average-price
                                              "QQQ"
                                              {:window 50}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 7 | 20d EMA > 200d SMA"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (exponential-moving-average-price
                                              "QQQ"
                                              {:window 20})
                                             (moving-average-price
                                              "QQQ"
                                              {:window 200}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 8 | 10d RSI > 50d RSI"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "QQQ" {:window 10})
                                             (rsi "QQQ" {:window 50}))
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 9 | 50d RSI < 55"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (rsi "QQQ" {:window 50})
                                             55)
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])
                                       (group
                                        "Group 10 | 100d RSI < 60"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (rsi "QQQ" {:window 100})
                                             60)
                                            [(group
                                              "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (current-price
                                                        "TQQQ")
                                                       (moving-average-price
                                                        "TQQQ"
                                                        {:window 20}))
                                                      [(weight-equal
                                                        [(filter
                                                          (rsi
                                                           {:window
                                                            10})
                                                          (select-top
                                                           1)
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
                                                            {:window
                                                             10})
                                                           31)
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")]
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "Holy Grail Revamped (168,48,2011)"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (current-price
                                                      "SPY")
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 200}))
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "VOX"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 62)
                                                                [(asset
                                                                  "VIXY"
                                                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                      nil)])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLK"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLF"
                                                                      {:window
                                                                       10})
                                                                     81)
                                                                    [(asset
                                                                      "VIXY"
                                                                      nil)]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         75)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "VIXY"
                                                                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
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
                                                                                  nil)])])])
                                                                           (asset
                                                                            "VIXY"
                                                                            "ProShares Trust - ProShares VIX Short-Term Futures ETF")])]
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
                                                                              nil)])])])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "QQQ"
                                                          {:window 60})
                                                         -12)
                                                        [(asset
                                                          "BIL"
                                                          nil)]
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
                                                                  nil)])])])])])])])])])
                                               (group
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
                                                     (asset
                                                      "XLU"
                                                      nil)])])])])])])])])])])
                                 (group
                                  "Overcompensating Chaos (OCFR -> HG) (400,47,2011)"
                                  [(weight-equal
                                    [(if
                                      (> (rsi "VTV" {:window 10}) 79)
                                      [(asset "VIXY" nil)]
                                      [(weight-equal
                                        [(if
                                          (>
                                           (rsi "XLF" {:window 10})
                                           80)
                                          [(asset "VIXY" nil)]
                                          [(weight-equal
                                            [(if
                                              (>
                                               (rsi "XLY" {:window 10})
                                               80)
                                              [(asset "VIXY" nil)]
                                              [(weight-equal
                                                [(if
                                                  (<
                                                   (rsi
                                                    "SPY"
                                                    {:window 10})
                                                   30)
                                                  [(asset "UPRO" nil)]
                                                  [(group
                                                    "Overcompensating Frontrunner"
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "IEF"
                                                          {:window 20})
                                                         (rsi
                                                          "PSQ"
                                                          {:window
                                                           60}))
                                                        [(weight-equal
                                                          [(filter
                                                            (stdev-return
                                                             {:window
                                                              12})
                                                            (select-top
                                                             1)
                                                            [(group
                                                              "MAX DD: TQQQ vs UVXY"
                                                              [(weight-equal
                                                                [(filter
                                                                  (max-drawdown
                                                                   {:window
                                                                    11})
                                                                  (select-bottom
                                                                   1)
                                                                  [(asset
                                                                    "TQQQ"
                                                                    "ProShares UltraPro QQQ")
                                                                   (asset
                                                                    "UVXY"
                                                                    "ProShares Ultra VIX Short-Term Futures ETF")])])])
                                                             (group
                                                              "MAX DD: TQQQ vs TECL"
                                                              [(weight-equal
                                                                [(filter
                                                                  (max-drawdown
                                                                   {:window
                                                                    10})
                                                                  (select-bottom
                                                                   1)
                                                                  [(asset
                                                                    "TQQQ"
                                                                    "ProShares UltraPro QQQ")
                                                                   (asset
                                                                    "TECL"
                                                                    "Direxion Shares ETF Trust - Direxion Daily Technology Bull 3X Shares")])])])
                                                             (group
                                                              "MAX DD: TQQQ vs UPRO"
                                                              [(weight-equal
                                                                [(filter
                                                                  (max-drawdown
                                                                   {:window
                                                                    9})
                                                                  (select-bottom
                                                                   1)
                                                                  [(asset
                                                                    "TQQQ"
                                                                    "ProShares UltraPro QQQ")
                                                                   (asset
                                                                    "UPRO"
                                                                    "ProShares UltraPro S&P500")])])])])])]
                                                        [(group
                                                          "Holy Grail Revamped | Safe Sectors Mod"
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
                                                                    [(asset
                                                                      "TQQQ"
                                                                      nil)]
                                                                    [(group
                                                                      "Safe Sectors or Bonds (61,29,2007)"
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (rsi
                                                                           {:window
                                                                            10})
                                                                          (select-bottom
                                                                           1)
                                                                          [(asset
                                                                            "BSV"
                                                                            nil)
                                                                           (asset
                                                                            "TLT"
                                                                            nil)
                                                                           (asset
                                                                            "LQD"
                                                                            nil)
                                                                           (asset
                                                                            "VBF"
                                                                            nil)
                                                                           (asset
                                                                            "XLP"
                                                                            nil)
                                                                           (asset
                                                                            "UGE"
                                                                            nil)
                                                                           (asset
                                                                            "XLV"
                                                                            nil)
                                                                           (asset
                                                                            "XLU"
                                                                            nil)])])])])])])]
                                                              [(weight-equal
                                                                [(if
                                                                  (<
                                                                   (cumulative-return
                                                                    "QQQ"
                                                                    {:window
                                                                     60})
                                                                   -12)
                                                                  [(group
                                                                    "Safe Sectors or Bonds (61,29,2007)"
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (rsi
                                                                         {:window
                                                                          10})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "BSV"
                                                                          nil)
                                                                         (asset
                                                                          "TLT"
                                                                          nil)
                                                                         (asset
                                                                          "LQD"
                                                                          nil)
                                                                         (asset
                                                                          "VBF"
                                                                          nil)
                                                                         (asset
                                                                          "XLP"
                                                                          nil)
                                                                         (asset
                                                                          "UGE"
                                                                          nil)
                                                                         (asset
                                                                          "XLV"
                                                                          nil)
                                                                         (asset
                                                                          "XLU"
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
                                                                          [(group
                                                                            "Safe Sectors or Bonds (61,29,2007)"
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (rsi
                                                                                 {:window
                                                                                  10})
                                                                                (select-bottom
                                                                                 1)
                                                                                [(asset
                                                                                  "BSV"
                                                                                  nil)
                                                                                 (asset
                                                                                  "TLT"
                                                                                  nil)
                                                                                 (asset
                                                                                  "LQD"
                                                                                  nil)
                                                                                 (asset
                                                                                  "VBF"
                                                                                  nil)
                                                                                 (asset
                                                                                  "XLP"
                                                                                  nil)
                                                                                 (asset
                                                                                  "UGE"
                                                                                  nil)
                                                                                 (asset
                                                                                  "XLV"
                                                                                  nil)
                                                                                 (asset
                                                                                  "XLU"
                                                                                  nil)])])])]
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
                                                                                [(group
                                                                                  "Safe Sectors or Bonds (61,29,2007)"
                                                                                  [(weight-equal
                                                                                    [(filter
                                                                                      (rsi
                                                                                       {:window
                                                                                        10})
                                                                                      (select-bottom
                                                                                       1)
                                                                                      [(asset
                                                                                        "BSV"
                                                                                        nil)
                                                                                       (asset
                                                                                        "TLT"
                                                                                        nil)
                                                                                       (asset
                                                                                        "LQD"
                                                                                        nil)
                                                                                       (asset
                                                                                        "VBF"
                                                                                        nil)
                                                                                       (asset
                                                                                        "XLP"
                                                                                        nil)
                                                                                       (asset
                                                                                        "UGE"
                                                                                        nil)
                                                                                       (asset
                                                                                        "XLV"
                                                                                        nil)
                                                                                       (asset
                                                                                        "XLU"
                                                                                        nil)])])])])])])])])]
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
                                                                            "Safe Sectors or Bonds (61,29,2007)"
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (rsi
                                                                                 {:window
                                                                                  10})
                                                                                (select-bottom
                                                                                 1)
                                                                                [(asset
                                                                                  "BSV"
                                                                                  nil)
                                                                                 (asset
                                                                                  "TLT"
                                                                                  nil)
                                                                                 (asset
                                                                                  "LQD"
                                                                                  nil)
                                                                                 (asset
                                                                                  "VBF"
                                                                                  nil)
                                                                                 (asset
                                                                                  "XLP"
                                                                                  nil)
                                                                                 (asset
                                                                                  "UGE"
                                                                                  nil)
                                                                                 (asset
                                                                                  "XLV"
                                                                                  nil)
                                                                                 (asset
                                                                                  "XLU"
                                                                                  nil)])])])]
                                                                          [(asset
                                                                            "SQQQ"
                                                                            nil)])])])])])])])])])])])])])])])])])])])])])])]))])])])])])])])])])])])])])
  0.25
  (group
   "Rain's Concise EM Leverage -> Safe Sectors (177,53,2008)"
   [(weight-equal
     [(if
       (< (rsi "EEM" {:window 14}) 30)
       [(asset "EDC" nil)]
       [(if
         (> (rsi "EEM" {:window 10}) 80)
         [(asset "EDZ" nil)]
         [(if
           (>
            (current-price "SHV")
            (moving-average-price "SHV" {:window 50}))
           [(if
             (>
              (current-price "EEM")
              (moving-average-price "EEM" {:window 200}))
             [(if
               (> (rsi "MMT" {:window 10}) (rsi "XLU" {:window 10}))
               [(if
                 (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IEI" {:window 10})
                      (rsi "IWM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
                         [(asset "EDC" nil)]
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(weight-equal
                         [(asset "EDZ" nil)
                          (group
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
                                (asset "UGE" nil)])])])])])])]
                   [(if
                     (>
                      (rsi "IEI" {:window 10})
                      (rsi "IWM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
                       [(weight-equal
                         [(asset "EDC" nil)
                          (group
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
                                (asset "UGE" nil)])])])])]
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
                              (asset "UGE" nil)])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
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
                              (asset "UGE" nil)])])])]
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
                         [(asset "EDZ" nil)])])])])]
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IEI" {:window 10})
                      (rsi "IWM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
                       [(weight-equal
                         [(asset "EDC" nil)
                          (group
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
                                (asset "UGE" nil)])])])])]
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
                              (asset "UGE" nil)])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
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
                              (asset "UGE" nil)])])])]
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
                         [(asset "EDZ" nil)])])])]
                   [(if
                     (>
                      (rsi "IEI" {:window 10})
                      (rsi "IWM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(asset "EDZ" nil)])])])])]
               [(if
                 (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IEI" {:window 10})
                      (rsi "IWM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
                       [(weight-equal
                         [(asset "EDC" nil)
                          (group
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
                                (asset "UGE" nil)])])])])]
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
                              (asset "UGE" nil)])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
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
                              (asset "UGE" nil)])])])]
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
                         [(asset "EDZ" nil)])])])]
                   [(if
                     (>
                      (rsi "IEI" {:window 10})
                      (rsi "IWM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(asset "EDZ" nil)])])])]
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IEI" {:window 10})
                      (rsi "IWM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(asset "EDZ" nil)])])]
                   [(if
                     (>
                      (rsi "IEI" {:window 10})
                      (rsi "IWM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "DIA" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(weight-equal
                         [(asset "EDZ" nil)
                          (group
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
                                (asset "UGE" nil)])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DBE" {:window 10}))
                       [(weight-equal
                         [(asset "EDZ" nil)
                          (group
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
                                (asset "UGE" nil)])])])])]
                       [(asset "EDZ" nil)])])])])])]
             [(if
               (> (rsi "MMT" {:window 10}) (rsi "XLU" {:window 10}))
               [(if
                 (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IGIB" {:window 15})
                      (rsi "EEM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(asset "EDC" nil)]
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 15})
                      (rsi "EEM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(asset "EDC" nil)]
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(asset "EDZ" nil)])])])])]
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IGIB" {:window 15})
                      (rsi "EEM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(asset "EDC" nil)]
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(asset "EDZ" nil)])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 15})
                      (rsi "EEM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(asset "EDZ" nil)])])])])])]
               [(if
                 (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IGIB" {:window 15})
                      (rsi "EEM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(asset "EDC" nil)]
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(asset "EDZ" nil)])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 15})
                      (rsi "EEM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(asset "EDZ" nil)])])])])]
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IGIB" {:window 15})
                      (rsi "EEM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(asset "EDZ" nil)])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 15})
                      (rsi "EEM" {:window 15}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(asset "EDZ" nil)])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
                         [(asset "EDZ" nil)])])])])])])])]
           [(if
             (>
              (current-price "EEM")
              (moving-average-price "EEM" {:window 200}))
             [(if
               (> (rsi "MMT" {:window 10}) (rsi "XLU" {:window 10}))
               [(if
                 (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "DBE" {:window 10}))
                     [(if
                       (>
                        (rsi "IEF" {:window 10})
                        (rsi "DIA" {:window 10}))
                       [(asset "EDC" nil)]
                       [(weight-equal
                         [(asset "EDC" nil)
                          (group
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
                                (asset "UGE" nil)])])])])])]
                     [(if
                       (>
                        (rsi "IEF" {:window 10})
                        (rsi "DIA" {:window 10}))
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
                              (asset "UGE" nil)])])])]
                       [(weight-equal
                         [(asset "EDZ" nil)
                          (group
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
                                (asset "UGE" nil)])])])])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "DBE" {:window 10}))
                     [(if
                       (>
                        (rsi "IEF" {:window 10})
                        (rsi "DIA" {:window 10}))
                       [(weight-equal
                         [(asset "EDC" nil)
                          (group
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
                                (asset "UGE" nil)])])])])]
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
                              (asset "UGE" nil)])])])])]
                     [(weight-equal
                       [(asset "EDZ" nil)
                        (group
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
                              (asset "UGE" nil)])])])])])])]
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "DBE" {:window 10}))
                     [(if
                       (>
                        (rsi "IEF" {:window 10})
                        (rsi "DIA" {:window 10}))
                       [(weight-equal
                         [(asset "EDC" nil)
                          (group
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
                                (asset "UGE" nil)])])])])]
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
                              (asset "UGE" nil)])])])])]
                     [(weight-equal
                       [(asset "EDZ" nil)
                        (group
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
                              (asset "UGE" nil)])])])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "DBE" {:window 10}))
                     [(if
                       (>
                        (rsi "IEF" {:window 10})
                        (rsi "DIA" {:window 10}))
                       [(weight-equal
                         [(asset "EDC" nil)
                          (group
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
                                (asset "UGE" nil)])])])])]
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
                              (asset "UGE" nil)])])])])]
                     [(asset "EDZ" nil)])])])]
               [(if
                 (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "DBE" {:window 10}))
                     [(if
                       (>
                        (rsi "IEF" {:window 10})
                        (rsi "DIA" {:window 10}))
                       [(weight-equal
                         [(asset "EDC" nil)
                          (group
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
                                (asset "UGE" nil)])])])])]
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
                              (asset "UGE" nil)])])])])]
                     [(weight-equal
                       [(asset "EDZ" nil)
                        (group
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
                              (asset "UGE" nil)])])])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "DBE" {:window 10}))
                     [(if
                       (>
                        (rsi "IEF" {:window 10})
                        (rsi "DIA" {:window 10}))
                       [(weight-equal
                         [(asset "EDC" nil)
                          (group
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
                                (asset "UGE" nil)])])])])]
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
                              (asset "UGE" nil)])])])])]
                     [(asset "EDZ" nil)])])]
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "DBE" {:window 10}))
                     [(if
                       (>
                        (rsi "IEF" {:window 10})
                        (rsi "DIA" {:window 10}))
                       [(weight-equal
                         [(asset "EDC" nil)
                          (group
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
                                (asset "UGE" nil)])])])])]
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
                              (asset "UGE" nil)])])])])]
                     [(asset "EDZ" nil)])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "DBE" {:window 10}))
                     [(if
                       (>
                        (rsi "IEF" {:window 10})
                        (rsi "DIA" {:window 10}))
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
                              (asset "UGE" nil)])])])]
                       [(weight-equal
                         [(asset "EDZ" nil)
                          (group
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
                                (asset "UGE" nil)])])])])])]
                     [(asset "EDZ" nil)])])])])]
             [(if
               (> (rsi "MMT" {:window 10}) (rsi "XLU" {:window 10}))
               [(if
                 (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "SPY" {:window 10}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(asset "EDC" nil)]
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "SPY" {:window 10}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(asset "EDC" nil)]
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(asset "EDZ" nil)])])])])]
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "SPY" {:window 10}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(asset "EDC" nil)]
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(asset "EDZ" nil)])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "SPY" {:window 10}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
                         [(asset "EDZ" nil)])])])])])]
               [(if
                 (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                 [(if
                   (>
                    (rsi "MHD" {:window 10})
                    (rsi "XLP" {:window 10}))
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "SPY" {:window 10}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(asset "EDC" nil)]
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(asset "EDZ" nil)])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "SPY" {:window 10}))
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDC" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
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
                                (asset "UGE" nil)])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])])]
                     [(if
                       (>
                        (rsi "IGIB" {:window 10})
                        (rsi "DLN" {:window 10}))
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
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
                                (asset "UGE" nil)])])])]
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])])]
                       [(if
                         (>
                          (rsi "ISCB" {:window 10})
                          (rsi "IWM" {:window 10}))
                         [(weight-equal
                           [(asset "EDZ" nil)
                            (group
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
                                  (asset "UGE" nil)])])])])]
                         [(asset "EDZ" nil)])])])])]
                 [(if
                   (>
                    (rsi "IGIB" {:window 10})
                    (rsi "SPY" {:window 10}))
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "DLN" {:window 10}))
                     [(if
                       (>
                        (rsi "ISCB" {:window 10})
                        (rsi "IWM" {:window 10}))
                       [(weight-equal
                         [(asset "EDC" nil)
                          (group
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
                                (asset "UGE" nil)])])])])]
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
                              (asset "UGE" nil)])])])])]
                     [(if
                       (>
                        (rsi "ISCB" {:window 10})
                        (rsi "IWM" {:window 10}))
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
                              (asset "UGE" nil)])])])]
                       [(weight-equal
                         [(asset "EDZ" nil)
                          (group
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
                                (asset "UGE" nil)])])])])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "DLN" {:window 10}))
                     [(if
                       (>
                        (rsi "ISCB" {:window 10})
                        (rsi "IWM" {:window 10}))
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
                              (asset "UGE" nil)])])])]
                       [(weight-equal
                         [(asset "EDZ" nil)
                          (group
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
                                (asset "UGE" nil)])])])])])]
                     [(if
                       (>
                        (rsi "ISCB" {:window 10})
                        (rsi "IWM" {:window 10}))
                       [(weight-equal
                         [(asset "EDZ" nil)
                          (group
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
                                (asset "UGE" nil)])])])])]
                       [(asset "EDZ" nil)])])])])])])])])])])])))
