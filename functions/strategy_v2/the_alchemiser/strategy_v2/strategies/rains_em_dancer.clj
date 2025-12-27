(defsymphony
 "Rain's Unified EM Leverage -> Safe Sectors | 25% EDC/YINN Dancer"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "Rain's Unified EM Leverage -> Safe Sectors | 25% EDC/YINN Dancer (166,50,2010)"
    [(weight-specified
      0.25
      (group
       "EDC/YINN Dancer"
       [(weight-equal
         [(if
           (< (rsi "EEM" {:window 14}) 28)
           [(asset
             "EDC"
             "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")]
           [(weight-equal
             [(if
               (> (rsi "EEM" {:window 14}) 75)
               [(asset
                 "BIL"
                 "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")]
               [(weight-equal
                 [(if
                   (>
                    (current-price "SHV")
                    (moving-average-price "SHV" {:window 160}))
                   [(weight-equal
                     [(if
                       (>
                        (current-price "EEM")
                        (moving-average-price "EEM" {:window 220}))
                       [(group
                         "IEI vs IWM"
                         [(weight-equal
                           [(if
                             (>
                              (rsi "IEI" {:window 10})
                              (rsi "IWM" {:window 12}))
                             [(weight-equal
                               [(filter
                                 (cumulative-return {:window 30})
                                 (select-top 1)
                                 [(asset
                                   "EDC"
                                   "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                                  (asset
                                   "YINN"
                                   "Direxion Shares ETF Trust - Direxion Daily FTSE China Bull 3X Shares")])])]
                             [(weight-equal
                               [(if
                                 (<
                                  (cumulative-return "EEM" {:window 5})
                                  -5)
                                 [(asset
                                   "BIL"
                                   "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")]
                                 [(weight-equal
                                   [(filter
                                     (cumulative-return {:window 2})
                                     (select-bottom 1)
                                     [(asset
                                       "YANG"
                                       "Direxion Shares ETF Trust - Direxion Daily FTSE China Bear -3X Shares")
                                      (asset
                                       "EDZ"
                                       "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")])])])])])])])]
                       [(weight-equal
                         [(if
                           (<
                            (current-price "EEM")
                            (moving-average-price "EEM" {:window 20}))
                           [(weight-equal
                             [(group
                               "IGIB vs SPY"
                               [(weight-equal
                                 [(if
                                   (>
                                    (rsi "IGIB" {:window 10})
                                    (rsi "SPY" {:window 10}))
                                   [(asset
                                     "EDC"
                                     "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                                    (asset
                                     "YINN"
                                     "Direxion Shares ETF Trust - Direxion Daily FTSE China Bull 3X Shares")]
                                   [(asset
                                     "EDZ"
                                     "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                                    (asset
                                     "YANG"
                                     "Direxion Shares ETF Trust - Direxion Daily FTSE China Bear -3X Shares")])])])])]
                           [(group
                             "IGIB vs EEM"
                             [(weight-equal
                               [(asset
                                 "EEM"
                                 "BlackRock Institutional Trust Company N.A. - iShares MSCI Emerging Markets ETF")
                                (asset
                                 "FXI"
                                 "BlackRock Institutional Trust Company N.A. - iShares China Large-Cap ETF")])])])])])])]
                   [(group
                     "IGIB vs SPY"
                     [(weight-equal
                       [(if
                         (>
                          (rsi "IGIB" {:window 10})
                          (rsi "SPY" {:window 10}))
                         [(asset
                           "EDC"
                           "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                          (asset
                           "YINN"
                           "Direxion Shares ETF Trust - Direxion Daily FTSE China Bull 3X Shares")]
                         [(asset
                           "EDZ"
                           "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                          (asset
                           "YANG"
                           "Direxion Shares ETF Trust - Direxion Daily FTSE China Bear -3X Shares")])])])])])])])])])])
      0.75
      (group
       "Leveraged Rain's Unified EM Signals | perspectiveseeker mashup | Safe Sectors mod (161,52,2008)"
       [(weight-equal
         [(if
           (< (rsi "EEM" {:window 14}) 30)
           [(asset
             "EDC"
             "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")]
           [(if
             (> (rsi "EEM" {:window 10}) 80)
             [(asset
               "EDZ"
               "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")]
             [(if
               (>
                (current-price "SHV")
                (moving-average-price "SHV" {:window 50}))
               [(if
                 (>
                  (current-price "EEM")
                  (moving-average-price "EEM" {:window 200}))
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
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(asset
                               "EDC"
                               "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")]
                             [(weight-specified
                               0.5714
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.4286
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.8332999999999999
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.16670000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.8332999999999999
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.16670000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.6667000000000001
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.3333
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.2857
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.7143
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
                                     (asset "UGE" nil)])])]))])])])]
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.5
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.5
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.1429
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
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
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
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
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.1429
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))])])])])]
                     [(if
                       (>
                        (rsi "IEF" {:window 10})
                        (rsi "DIA" {:window 10}))
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.5
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.5
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.1429
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
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
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
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
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.1429
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))])])])]
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
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
                             [(weight-specified
                               0.2857
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.7143
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.5714
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.4286
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
                                     (asset
                                      "UGE"
                                      nil)])])]))])])])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "DBE" {:window 10}))
                     [(if
                       (>
                        (rsi "IEF" {:window 10})
                        (rsi "DIA" {:window 10}))
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.5
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.5
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.1429
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
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
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
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
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.1429
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))])])])]
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
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
                             [(weight-specified
                               0.2857
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.7143
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.5714
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.4286
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
                                     (asset "UGE" nil)])])]))])])])])]
                     [(if
                       (>
                        (rsi "IEF" {:window 10})
                        (rsi "DIA" {:window 10}))
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
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
                             [(weight-specified
                               0.2857
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.7143
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.5714
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.4286
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
                                     (asset "UGE" nil)])])]))])])])]
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.5
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.7143
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.2857
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.6667000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.3333
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.8571
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.1429
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.6667000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.3333
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.8571
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.1429
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.8332999999999999
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.16670000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(asset
                               "EDZ"
                               "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")])])])])])])]
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
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(asset
                               "EDC"
                               "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")]
                             [(weight-specified
                               0.52
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.48
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.8095
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.1905
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.36
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.64
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.8095
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.1905
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.36
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.64
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.619
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.381
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.2
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8
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
                                     (asset "UGE" nil)])])]))])])])]
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.4286
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.04
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.96
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.23809999999999998
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.7619
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.12
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.88
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.23809999999999998
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.7619
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.12
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.88
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.047599999999999996
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.9523999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.28
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.72
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
                                     (asset "UGE" nil)])])]))])])])])]
                     [(if
                       (>
                        (rsi "ISCB" {:window 10})
                        (rsi "IWM" {:window 10}))
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.4286
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.04
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.96
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.23809999999999998
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.7619
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.12
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.88
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.23809999999999998
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.7619
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.12
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.88
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.047599999999999996
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.9523999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.28
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.72
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
                                     (asset "UGE" nil)])])]))])])])]
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.1429
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.44
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.56
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.6
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.4
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.6
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.4
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.5238
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.47619999999999996
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.76
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.24
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
                                     (asset
                                      "UGE"
                                      nil)])])]))])])])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "DLN" {:window 10}))
                     [(if
                       (>
                        (rsi "ISCB" {:window 10})
                        (rsi "IWM" {:window 10}))
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.7143
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.2857
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.28
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.72
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.5238
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.47619999999999996
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.12
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.88
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.5238
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.47619999999999996
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.12
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.88
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.04
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.96
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
                                     (asset "UGE" nil)])])]))])])])]
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.1429
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.2
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.047599999999999996
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.9523999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.36
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.64
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.047599999999999996
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.9523999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.36
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.64
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.23809999999999998
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.7619
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.52
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.48
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
                                     (asset "UGE" nil)])])]))])])])])]
                     [(if
                       (>
                        (rsi "ISCB" {:window 10})
                        (rsi "IWM" {:window 10}))
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.1429
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.2
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.047599999999999996
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.9523999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.36
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.64
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.047599999999999996
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.9523999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.36
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.64
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.23809999999999998
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.7619
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.52
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.48
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
                                     (asset "UGE" nil)])])]))])])])]
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.4286
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.68
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.32
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.619
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.381
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.84
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.16
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.619
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.381
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.84
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.16
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.8095
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.1905
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
                                     (asset "UGE" nil)])])]))]
                             [(asset
                               "EDZ"
                               "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")])])])])])])])]
               [(if
                 (>
                  (current-price "EEM")
                  (moving-average-price "EEM" {:window 200}))
                 [(if
                   (>
                    (rsi "IGIB" {:window 10})
                    (rsi "DBE" {:window 10}))
                   [(if
                     (>
                      (rsi "IEF" {:window 10})
                      (rsi "DIA" {:window 10}))
                     [(if
                       (>
                        (rsi "MMT" {:window 10})
                        (rsi "XLU" {:window 10}))
                       [(if
                         (>
                          (rsi "PIM" {:window 10})
                          (rsi "BBH" {:window 10}))
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(asset
                             "EDC"
                             "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")]
                           [(weight-specified
                             0.4545
                             (asset
                              "EDC"
                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                             0.5455
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
                                   (asset "UGE" nil)])])]))])]
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.7778
                             (asset
                              "EDC"
                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                             0.22219999999999998
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.2727
                             (asset
                              "EDC"
                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                             0.7273000000000001
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
                                   (asset "UGE" nil)])])]))])])]
                       [(if
                         (>
                          (rsi "PIM" {:window 10})
                          (rsi "BBH" {:window 10}))
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.7778
                             (asset
                              "EDC"
                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                             0.22219999999999998
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.2727
                             (asset
                              "EDC"
                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                             0.7273000000000001
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
                                   (asset "UGE" nil)])])]))])]
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.5556
                             (asset
                              "EDC"
                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                             0.44439999999999996
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.0909
                             (asset
                              "EDC"
                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                             0.9091
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
                                   (asset "UGE" nil)])])]))])])])]
                     [(if
                       (>
                        (rsi "MMT" {:window 10})
                        (rsi "XLU" {:window 10}))
                       [(if
                         (>
                          (rsi "PIM" {:window 10})
                          (rsi "BBH" {:window 10}))
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.3333
                             (asset
                              "EDC"
                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                             0.6667000000000001
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.0909
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.9091
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
                                   (asset "UGE" nil)])])]))])]
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.11109999999999999
                             (asset
                              "EDC"
                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                             0.8889
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.2727
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.7273000000000001
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
                                   (asset "UGE" nil)])])]))])])]
                       [(if
                         (>
                          (rsi "PIM" {:window 10})
                          (rsi "BBH" {:window 10}))
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.11109999999999999
                             (asset
                              "EDC"
                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                             0.8889
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.2727
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.7273000000000001
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
                                   (asset "UGE" nil)])])]))])]
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.11109999999999999
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.8889
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.4545
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.5455
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
                                   (asset "UGE" nil)])])]))])])])])]
                   [(if
                     (>
                      (rsi "IEF" {:window 10})
                      (rsi "DIA" {:window 10}))
                     [(if
                       (>
                        (rsi "MMT" {:window 10})
                        (rsi "XLU" {:window 10}))
                       [(if
                         (>
                          (rsi "PIM" {:window 10})
                          (rsi "BBH" {:window 10}))
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.3333
                             (asset
                              "EDC"
                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                             0.6667000000000001
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.0909
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.9091
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
                                   (asset "UGE" nil)])])]))])]
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.11109999999999999
                             (asset
                              "EDC"
                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                             0.8889
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.2727
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.7273000000000001
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
                                   (asset "UGE" nil)])])]))])])]
                       [(if
                         (>
                          (rsi "PIM" {:window 10})
                          (rsi "BBH" {:window 10}))
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.11109999999999999
                             (asset
                              "EDC"
                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                             0.8889
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.2727
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.7273000000000001
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
                                   (asset "UGE" nil)])])]))])]
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.11109999999999999
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.8889
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.4545
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.5455
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
                                   (asset "UGE" nil)])])]))])])])]
                     [(if
                       (>
                        (rsi "MMT" {:window 10})
                        (rsi "XLU" {:window 10}))
                       [(if
                         (>
                          (rsi "PIM" {:window 10})
                          (rsi "BBH" {:window 10}))
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.3333
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.6667000000000001
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.6364
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.3636
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
                                   (asset "UGE" nil)])])]))])]
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.5556
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.44439999999999996
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.8181999999999999
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.1818
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
                                   (asset "UGE" nil)])])]))])])]
                       [(if
                         (>
                          (rsi "PIM" {:window 10})
                          (rsi "BBH" {:window 10}))
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.5556
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.44439999999999996
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
                                   (asset "UGE" nil)])])]))]
                           [(weight-specified
                             0.8181999999999999
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.1818
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
                                   (asset "UGE" nil)])])]))])]
                         [(if
                           (>
                            (rsi "MHD" {:window 10})
                            (rsi "XLP" {:window 10}))
                           [(weight-specified
                             0.7778
                             (asset
                              "EDZ"
                              "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                             0.22219999999999998
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
                                   (asset "UGE" nil)])])]))]
                           [(asset
                             "EDZ"
                             "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")])])])])])]
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
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(asset
                               "EDC"
                               "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")]
                             [(weight-specified
                               0.5714
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.4286
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.8332999999999999
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.16670000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.8332999999999999
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.16670000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.6667000000000001
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.3333
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.2857
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.7143
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
                                     (asset "UGE" nil)])])]))])])])]
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.5
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.5
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.1429
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
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
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
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
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.1429
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))])])])])]
                     [(if
                       (>
                        (rsi "ISCB" {:window 10})
                        (rsi "IWM" {:window 10}))
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.5
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.5
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.1429
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
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
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
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
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.1429
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))])])])]
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
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
                             [(weight-specified
                               0.2857
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.7143
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.5714
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.4286
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
                                     (asset
                                      "UGE"
                                      nil)])])]))])])])])])]
                   [(if
                     (>
                      (rsi "IGIB" {:window 10})
                      (rsi "DLN" {:window 10}))
                     [(if
                       (>
                        (rsi "ISCB" {:window 10})
                        (rsi "IWM" {:window 10}))
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.5
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.5
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.1429
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
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
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
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
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDC"
                                "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.1429
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8571
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
                                     (asset "UGE" nil)])])]))])])])]
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
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
                             [(weight-specified
                               0.2857
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.7143
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.5714
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.4286
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
                                     (asset "UGE" nil)])])]))])])])])]
                     [(if
                       (>
                        (rsi "ISCB" {:window 10})
                        (rsi "IWM" {:window 10}))
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
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
                             [(weight-specified
                               0.2857
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.7143
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.16670000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.8332999999999999
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.4286
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5714
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.3333
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.6667000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.5714
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.4286
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
                                     (asset "UGE" nil)])])]))])])])]
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.5
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.5
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.7143
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.2857
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.6667000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.3333
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.8571
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.1429
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
                                     (asset "UGE" nil)])])]))])])]
                         [(if
                           (>
                            (rsi "PIM" {:window 10})
                            (rsi "BBH" {:window 10}))
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.6667000000000001
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.3333
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
                                     (asset "UGE" nil)])])]))]
                             [(weight-specified
                               0.8571
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.1429
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
                                     (asset "UGE" nil)])])]))])]
                           [(if
                             (>
                              (rsi "MHD" {:window 10})
                              (rsi "XLP" {:window 10}))
                             [(weight-specified
                               0.8332999999999999
                               (asset
                                "EDZ"
                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                               0.16670000000000001
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
                                     (asset "UGE" nil)])])]))]
                             [(asset
                               "EDZ"
                               "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")])])])])])])])])])])])]))])]))
