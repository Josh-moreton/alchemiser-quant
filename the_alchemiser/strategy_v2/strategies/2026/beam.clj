(defsymphony
 "BEAM Chain Algo Test 1 (Buy Copy)"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "Beam Filter: XLK, XLP, XLE 75/4.3"
    [(weight-equal
      [(if
        (>
         (cumulative-return "IWM" {:window 5})
         (cumulative-return "USO" {:window 5}))
        [(weight-equal
          [(if
            (>
             (moving-average-return "XLI" {:window 20})
             (moving-average-return "IWM" {:window 40}))
            [(asset
              "XLP"
              "SSgA Active Trust - Consumer Staples Select Sector SPDR")]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "SOXX" {:window 65})
                 (cumulative-return "IWM" {:window 30}))
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "IWM" {:window 5})
                     (cumulative-return "XLE" {:window 10}))
                    [(asset
                      "XLE"
                      "SSgA Active Trust - The Energy Select Sector SPDR Fund")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "XLI" {:window 80})
                         (cumulative-return "XLE" {:window 30}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "DIA" {:window 30})
                             (cumulative-return "USO" {:window 60}))
                            [(asset
                              "XLK"
                              "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "XLI" {:window 80})
                     (cumulative-return "XLE" {:window 30}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "DIA" {:window 30})
                         (cumulative-return "USO" {:window 60}))
                        [(asset
                          "XLK"
                          "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
        [(weight-equal
          [(if
            (>
             (cumulative-return "SOXX" {:window 65})
             (cumulative-return "IWM" {:window 30}))
            [(weight-equal
              [(if
                (>
                 (cumulative-return "IWM" {:window 5})
                 (cumulative-return "XLE" {:window 10}))
                [(asset
                  "XLE"
                  "SSgA Active Trust - The Energy Select Sector SPDR Fund")]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "XLI" {:window 80})
                     (cumulative-return "XLE" {:window 30}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "DIA" {:window 30})
                         (cumulative-return "USO" {:window 60}))
                        [(asset
                          "XLK"
                          "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "XLI" {:window 80})
                 (cumulative-return "XLE" {:window 30}))
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "DIA" {:window 30})
                     (cumulative-return "USO" {:window 60}))
                    [(asset
                      "XLK"
                      "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                [(asset
                  "BIL"
                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
   (group
    "Beam Filter: BITO, IEF 85/23"
    [(weight-equal
      [(if
        (>
         (cumulative-return "EWG" {:window 45})
         (cumulative-return "XLI" {:window 75}))
        [(weight-equal
          [(if
            (>
             (cumulative-return "EFA" {:window 55})
             (cumulative-return "TLT" {:window 75}))
            [(asset
              "IEF"
              "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "XLY" {:window 45})
                 (cumulative-return "IWM" {:window 35}))
                [(weight-equal
                  [(if
                    (>
                     (stdev-return "XLF" {:window 10})
                     (stdev-return "XLF" {:window 40}))
                    [(asset
                      "BITO"
                      "ProShares Trust - ProShares Bitcoin ETF")]
                    [(weight-equal
                      [(if
                        (>
                         (moving-average-return "HYG" {:window 90})
                         (moving-average-return "SHY" {:window 90}))
                        [(weight-equal
                          [(if
                            (>
                             (stdev-return "IWM" {:window 30})
                             (stdev-return "IWM" {:window 40}))
                            [(asset
                              "IEF"
                              "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                [(weight-equal
                  [(if
                    (>
                     (moving-average-return "HYG" {:window 90})
                     (moving-average-return "SHY" {:window 90}))
                    [(weight-equal
                      [(if
                        (>
                         (stdev-return "IWM" {:window 30})
                         (stdev-return "IWM" {:window 40}))
                        [(asset
                          "IEF"
                          "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
        [(weight-equal
          [(if
            (>
             (cumulative-return "XLY" {:window 45})
             (cumulative-return "IWM" {:window 35}))
            [(weight-equal
              [(if
                (>
                 (stdev-return "XLF" {:window 10})
                 (stdev-return "XLF" {:window 40}))
                [(asset
                  "BITO"
                  "ProShares Trust - ProShares Bitcoin ETF")]
                [(weight-equal
                  [(if
                    (>
                     (moving-average-return "HYG" {:window 90})
                     (moving-average-return "SHY" {:window 90}))
                    [(weight-equal
                      [(if
                        (>
                         (stdev-return "IWM" {:window 30})
                         (stdev-return "IWM" {:window 40}))
                        [(asset
                          "IEF"
                          "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
            [(weight-equal
              [(if
                (>
                 (moving-average-return "HYG" {:window 90})
                 (moving-average-return "SHY" {:window 90}))
                [(weight-equal
                  [(if
                    (>
                     (stdev-return "IWM" {:window 30})
                     (stdev-return "IWM" {:window 40}))
                    [(asset
                      "IEF"
                      "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                [(asset
                  "BIL"
                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
   (group
    "Beam Filter: HYG, BTAL 28/9.5"
    [(weight-equal
      [(if
        (>
         (stdev-return "IWM" {:window 30})
         (stdev-return "QQQ" {:window 40}))
        [(weight-equal
          [(if
            (>
             (cumulative-return "HYG" {:window 75})
             (cumulative-return "QQQ" {:window 5}))
            [(asset
              "HYG"
              "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "QQQ" {:window 5})
                 (cumulative-return "HYG" {:window 55}))
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "IWM" {:window 85})
                     (cumulative-return "BTAL" {:window 65}))
                    [(asset
                      "BTAL"
                      "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "BTAL" {:window 60})
                         (cumulative-return "BTAL" {:window 55}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "BTAL" {:window 90})
                             (cumulative-return "IWM" {:window 10}))
                            [(asset
                              "HYG"
                              "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                            [(weight-equal
                              [(asset
                                "BIL"
                                "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "BTAL" {:window 60})
                     (cumulative-return "BTAL" {:window 55}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "BTAL" {:window 90})
                         (cumulative-return "IWM" {:window 10}))
                        [(asset
                          "HYG"
                          "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                        [(weight-equal
                          [(asset
                            "BIL"
                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
        [(weight-equal
          [(if
            (>
             (cumulative-return "QQQ" {:window 5})
             (cumulative-return "HYG" {:window 55}))
            [(weight-equal
              [(if
                (>
                 (cumulative-return "IWM" {:window 85})
                 (cumulative-return "BTAL" {:window 65}))
                [(asset
                  "BTAL"
                  "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "BTAL" {:window 60})
                     (cumulative-return "BTAL" {:window 55}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "BTAL" {:window 90})
                         (cumulative-return "IWM" {:window 10}))
                        [(asset
                          "HYG"
                          "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                        [(weight-equal
                          [(asset
                            "BIL"
                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "BTAL" {:window 60})
                 (cumulative-return "BTAL" {:window 55}))
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "BTAL" {:window 90})
                     (cumulative-return "IWM" {:window 10}))
                    [(asset
                      "HYG"
                      "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                    [(weight-equal
                      [(asset
                        "BIL"
                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                [(asset
                  "BIL"
                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
   (group
    "Beam Filter: GLD, SOXX, BTAL 124/17.5"
    [(weight-equal
      [(if
        (>
         (cumulative-return "IWM" {:window 80})
         (cumulative-return "EWG" {:window 75}))
        [(weight-equal
          [(if
            (>
             (moving-average-return "QQQ" {:window 60})
             (moving-average-return "IWM" {:window 100}))
            [(asset
              "BTAL"
              "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "DIA" {:window 55})
                 (cumulative-return "IWM" {:window 40}))
                [(weight-equal
                  [(if
                    (> (cumulative-return "EFA" {:window 20}) -8)
                    [(asset
                      "UGL"
                      "ProShares Trust - ProShares Ultra Gold 2x Shares")]
                    [(weight-equal
                      [(if
                        (>
                         (stdev-return "EFA" {:window 50})
                         (stdev-return "EFA" {:window 30}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "IWM" {:window 70})
                             (cumulative-return "SOXX" {:window 50}))
                            [(asset
                              "SOXL"
                              "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                            [(weight-equal
                              [(asset
                                "BIL"
                                "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                [(weight-equal
                  [(if
                    (>
                     (stdev-return "EFA" {:window 50})
                     (stdev-return "EFA" {:window 30}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "IWM" {:window 70})
                         (cumulative-return "SOXX" {:window 50}))
                        [(asset
                          "SOXL"
                          "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                        [(weight-equal
                          [(asset
                            "BIL"
                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
        [(weight-equal
          [(if
            (>
             (cumulative-return "DIA" {:window 55})
             (cumulative-return "IWM" {:window 40}))
            [(weight-equal
              [(if
                (> (cumulative-return "EFA" {:window 20}) -8)
                [(asset
                  "UGL"
                  "ProShares Trust - ProShares Ultra Gold 2x Shares")]
                [(weight-equal
                  [(if
                    (>
                     (stdev-return "EFA" {:window 50})
                     (stdev-return "EFA" {:window 30}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "IWM" {:window 70})
                         (cumulative-return "SOXX" {:window 50}))
                        [(asset
                          "SOXL"
                          "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                        [(weight-equal
                          [(asset
                            "BIL"
                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
            [(weight-equal
              [(if
                (>
                 (stdev-return "EFA" {:window 50})
                 (stdev-return "EFA" {:window 30}))
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "IWM" {:window 70})
                     (cumulative-return "SOXX" {:window 50}))
                    [(asset
                      "SOXL"
                      "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                    [(weight-equal
                      [(asset
                        "BIL"
                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                [(asset
                  "BIL"
                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
   (group
    "Beam Filter: TMV, GLD 103/10"
    [(weight-equal
      [(if
        (>
         (cumulative-return "EWU" {:window 5})
         (cumulative-return "IEF" {:window 5}))
        [(weight-equal
          [(if
            (>
             (stdev-return "HYG" {:window 10})
             (moving-average-return "EWU" {:window 20}))
            [(asset "GLD" "SPDR Gold Trust - SPDR Gold Shares ETF")]
            [(weight-equal
              [(if
                (> (rsi "TLT" {:window 20}) (rsi "HYG" {:window 20}))
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "IEF" {:window 75})
                     (cumulative-return "EWU" {:window 80}))
                    [(asset
                      "TMV"
                      "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "TLT" {:window 80})
                         (cumulative-return "HYG" {:window 10}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "GLD" {:window 60})
                             8)
                            [(asset
                              "TMV"
                              "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "TLT" {:window 80})
                     (cumulative-return "HYG" {:window 10}))
                    [(weight-equal
                      [(if
                        (> (cumulative-return "GLD" {:window 60}) 8)
                        [(asset
                          "TMV"
                          "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
        [(weight-equal
          [(if
            (> (rsi "TLT" {:window 20}) (rsi "HYG" {:window 20}))
            [(weight-equal
              [(if
                (>
                 (cumulative-return "IEF" {:window 75})
                 (cumulative-return "EWU" {:window 80}))
                [(asset
                  "TMV"
                  "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "TLT" {:window 80})
                     (cumulative-return "HYG" {:window 10}))
                    [(weight-equal
                      [(if
                        (> (cumulative-return "GLD" {:window 60}) 8)
                        [(asset
                          "TMV"
                          "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "TLT" {:window 80})
                 (cumulative-return "HYG" {:window 10}))
                [(weight-equal
                  [(if
                    (> (cumulative-return "GLD" {:window 60}) 8)
                    [(asset
                      "TMV"
                      "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                [(asset
                  "BIL"
                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
   (group
    "Beam FIlter: SOXX, KMLM, HYG 156/21"
    [(weight-equal
      [(if
        (>
         (moving-average-return "HYG" {:window 90})
         (moving-average-return "XLF" {:window 60}))
        [(weight-equal
          [(if
            (>
             (cumulative-return "LQD" {:window 90})
             (cumulative-return "EFA" {:window 75}))
            [(asset
              "SOXL"
              "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
            [(weight-equal
              [(if
                (>
                 (stdev-return "LQD" {:window 20})
                 (stdev-return "HYG" {:window 30}))
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "HYG" {:window 90})
                     (cumulative-return "QQQ" {:window 15}))
                    [(asset
                      "HYG"
                      "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "QQQ" {:window 15})
                         (cumulative-return "LQD" {:window 30}))
                        [(weight-equal
                          [(if
                            (>
                             (rsi "IWM" {:window 5})
                             (rsi "DIA" {:window 10}))
                            [(asset
                              "KMLM"
                              "KraneShares Trust - KraneShares Mount Lucas Managed Futures Index Strategy ETF")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "QQQ" {:window 15})
                     (cumulative-return "LQD" {:window 30}))
                    [(weight-equal
                      [(if
                        (>
                         (rsi "IWM" {:window 5})
                         (rsi "DIA" {:window 10}))
                        [(asset
                          "KMLM"
                          "KraneShares Trust - KraneShares Mount Lucas Managed Futures Index Strategy ETF")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
        [(weight-equal
          [(if
            (>
             (stdev-return "LQD" {:window 20})
             (stdev-return "HYG" {:window 30}))
            [(weight-equal
              [(if
                (>
                 (cumulative-return "HYG" {:window 90})
                 (cumulative-return "QQQ" {:window 15}))
                [(asset
                  "HYG"
                  "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "QQQ" {:window 15})
                     (cumulative-return "LQD" {:window 30}))
                    [(weight-equal
                      [(if
                        (>
                         (rsi "IWM" {:window 5})
                         (rsi "DIA" {:window 10}))
                        [(asset
                          "KMLM"
                          "KraneShares Trust - KraneShares Mount Lucas Managed Futures Index Strategy ETF")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "QQQ" {:window 15})
                 (cumulative-return "LQD" {:window 30}))
                [(weight-equal
                  [(if
                    (>
                     (rsi "IWM" {:window 5})
                     (rsi "DIA" {:window 10}))
                    [(asset
                      "KMLM"
                      "KraneShares Trust - KraneShares Mount Lucas Managed Futures Index Strategy ETF")]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                [(asset
                  "BIL"
                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
   (group
    "Beam Filter: AIQ, ICLN, CIBR 64/9"
    [(weight-equal
      [(if
        (>
         (cumulative-return "XLF" {:window 25})
         (cumulative-return "CIBR" {:window 70}))
        [(weight-equal
          [(if
            (> (cumulative-return "AIQ" {:window 55}) 0)
            [(asset
              "CIBR"
              "First Trust Exchange-Traded Fund III - First Trust NASDAQ Cybersecurity ETF")]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "XLF" {:window 20})
                 (cumulative-return "DIA" {:window 85}))
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "XLI" {:window 25})
                     (cumulative-return "DIA" {:window 65}))
                    [(asset
                      "ICLN"
                      "BlackRock Institutional Trust Company N.A. - iShares Global Clean Energy ETF")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "XLK" {:window 25})
                         (cumulative-return "XLI" {:window 5}))
                        [(weight-equal
                          [(if
                            (>
                             (stdev-return "XLK" {:window 10})
                             (stdev-return "XLK" {:window 20}))
                            [(asset
                              "AIQ"
                              "Global X Funds - Global X Artificial Intelligence & Technology ETF")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "XLK" {:window 25})
                     (cumulative-return "XLI" {:window 5}))
                    [(weight-equal
                      [(if
                        (>
                         (stdev-return "XLK" {:window 10})
                         (stdev-return "XLK" {:window 20}))
                        [(asset
                          "AIQ"
                          "Global X Funds - Global X Artificial Intelligence & Technology ETF")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
        [(weight-equal
          [(if
            (>
             (cumulative-return "XLF" {:window 20})
             (cumulative-return "DIA" {:window 85}))
            [(weight-equal
              [(if
                (>
                 (cumulative-return "XLI" {:window 25})
                 (cumulative-return "DIA" {:window 65}))
                [(asset
                  "ICLN"
                  "BlackRock Institutional Trust Company N.A. - iShares Global Clean Energy ETF")]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "XLK" {:window 25})
                     (cumulative-return "XLI" {:window 5}))
                    [(weight-equal
                      [(if
                        (>
                         (stdev-return "XLK" {:window 10})
                         (stdev-return "XLK" {:window 20}))
                        [(asset
                          "AIQ"
                          "Global X Funds - Global X Artificial Intelligence & Technology ETF")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "XLK" {:window 25})
                 (cumulative-return "XLI" {:window 5}))
                [(weight-equal
                  [(if
                    (>
                     (stdev-return "XLK" {:window 10})
                     (stdev-return "XLK" {:window 20}))
                    [(asset
                      "AIQ"
                      "Global X Funds - Global X Artificial Intelligence & Technology ETF")]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                [(asset
                  "BIL"
                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
   (group
    "Beam Filter: GLD, QQQ 319/54"
    [(weight-equal
      [(if
        (>
         (cumulative-return "QQQ" {:window 90})
         (cumulative-return "XLK" {:window 70}))
        [(weight-equal
          [(if
            (>
             (moving-average-return "DIA" {:window 100})
             (moving-average-return "SHY" {:window 80}))
            [(asset
              "GDXU"
              "Bank of Montreal - MicroSectors Gold Miners 3X Leveraged ETN")]
            [(weight-equal
              [(group
                "TQQQ 1"
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "XLK" {:window 30})
                     (cumulative-return "DIA" {:window 5}))
                    [(weight-equal
                      [(if
                        (>
                         (rsi "XLK" {:window 25})
                         (rsi "DIA" {:window 30}))
                        [(asset
                          "TQQQ"
                          "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                        [(weight-equal
                          [(group
                            "TQQQ 2"
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "SMH" {:window 80})
                                 (cumulative-return
                                  "SMH"
                                  {:window 65}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "DIA"
                                      {:window 80})
                                     (cumulative-return
                                      "DIA"
                                      {:window 65}))
                                    [(asset
                                      "TQQQ"
                                      "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                    [(group
                      "TQQQ 2"
                      [(weight-equal
                        [(if
                          (>
                           (cumulative-return "SMH" {:window 80})
                           (cumulative-return "SMH" {:window 65}))
                          [(weight-equal
                            [(if
                              (>
                               (cumulative-return "DIA" {:window 80})
                               (cumulative-return "DIA" {:window 65}))
                              [(asset
                                "TQQQ"
                                "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                              [(asset
                                "BIL"
                                "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                          [(asset
                            "BIL"
                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
        [(group
          "TQQQ 1"
          [(weight-equal
            [(if
              (>
               (cumulative-return "XLK" {:window 30})
               (cumulative-return "DIA" {:window 5}))
              [(weight-equal
                [(if
                  (> (rsi "XLK" {:window 25}) (rsi "DIA" {:window 30}))
                  [(asset
                    "TQQQ"
                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                  [(weight-equal
                    [(group
                      "TQQQ 2"
                      [(weight-equal
                        [(if
                          (>
                           (cumulative-return "SMH" {:window 80})
                           (cumulative-return "SMH" {:window 65}))
                          [(weight-equal
                            [(if
                              (>
                               (cumulative-return "DIA" {:window 80})
                               (cumulative-return "DIA" {:window 65}))
                              [(asset
                                "TQQQ"
                                "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                              [(asset
                                "BIL"
                                "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                          [(asset
                            "BIL"
                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
              [(group
                "TQQQ 2"
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "SMH" {:window 80})
                     (cumulative-return "SMH" {:window 65}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "DIA" {:window 80})
                         (cumulative-return "DIA" {:window 65}))
                        [(asset
                          "TQQQ"
                          "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])
   (group
    "Beam Filter: GLD, CORP 32/5.6"
    [(weight-equal
      [(if
        (>
         (moving-average-return "QQQ" {:window 80})
         (moving-average-return "IWM" {:window 40}))
        [(weight-equal
          [(if
            (>
             (cumulative-return "GLD" {:window 50})
             (cumulative-return "GLD" {:window 60}))
            [(asset "GLD" "SPDR Gold Trust - SPDR Gold Shares ETF")]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "LQD" {:window 45})
                 (cumulative-return "CORP" {:window 45}))
                [(weight-equal
                  [(if
                    (> (rsi "CORP" {:window 5}) 40)
                    [(asset
                      "CORP"
                      "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "QQQ" {:window 90})
                         (cumulative-return "QQQ" {:window 70}))
                        [(weight-equal
                          [(if
                            (>
                             (rsi "EWG" {:window 15})
                             (rsi "EWU" {:window 20}))
                            [(asset
                              "GLD"
                              "SPDR Gold Trust - SPDR Gold Shares ETF")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "QQQ" {:window 90})
                     (cumulative-return "QQQ" {:window 70}))
                    [(weight-equal
                      [(if
                        (>
                         (rsi "EWG" {:window 15})
                         (rsi "EWU" {:window 20}))
                        [(asset
                          "GLD"
                          "SPDR Gold Trust - SPDR Gold Shares ETF")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
        [(weight-equal
          [(if
            (>
             (cumulative-return "LQD" {:window 45})
             (cumulative-return "CORP" {:window 45}))
            [(weight-equal
              [(if
                (> (rsi "CORP" {:window 5}) 40)
                [(asset
                  "CORP"
                  "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "QQQ" {:window 90})
                     (cumulative-return "QQQ" {:window 70}))
                    [(weight-equal
                      [(if
                        (>
                         (rsi "EWG" {:window 15})
                         (rsi "EWU" {:window 20}))
                        [(asset
                          "GLD"
                          "SPDR Gold Trust - SPDR Gold Shares ETF")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "QQQ" {:window 90})
                 (cumulative-return "QQQ" {:window 70}))
                [(weight-equal
                  [(if
                    (>
                     (rsi "EWG" {:window 15})
                     (rsi "EWU" {:window 20}))
                    [(asset
                      "GLD"
                      "SPDR Gold Trust - SPDR Gold Shares ETF")]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                [(asset
                  "BIL"
                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
   (group
    "Beam Filter: CORP, BTAL 28/6"
    [(weight-equal
      [(if
        (> (cumulative-return "HYG" {:window 15}) 0)
        [(weight-equal
          [(if
            (>
             (cumulative-return "HYG" {:window 90})
             (cumulative-return "HYG" {:window 80}))
            [(asset
              "CORP"
              "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "SHY" {:window 45})
                 (cumulative-return "SHY" {:window 50}))
                [(weight-equal
                  [(if
                    (>
                     (moving-average-return "IWM" {:window 100})
                     (moving-average-return "LQD" {:window 100}))
                    [(asset
                      "BTAL"
                      "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "LQD" {:window 70})
                         (cumulative-return "CORP" {:window 65}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "LQD" {:window 80})
                             (cumulative-return "CORP" {:window 80}))
                            [(asset
                              "CORP"
                              "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "LQD" {:window 70})
                     (cumulative-return "CORP" {:window 65}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "LQD" {:window 80})
                         (cumulative-return "CORP" {:window 80}))
                        [(asset
                          "CORP"
                          "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
        [(weight-equal
          [(if
            (>
             (cumulative-return "SHY" {:window 45})
             (cumulative-return "SHY" {:window 50}))
            [(weight-equal
              [(if
                (>
                 (moving-average-return "IWM" {:window 100})
                 (moving-average-return "LQD" {:window 100}))
                [(asset
                  "BTAL"
                  "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "LQD" {:window 70})
                     (cumulative-return "CORP" {:window 65}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "LQD" {:window 80})
                         (cumulative-return "CORP" {:window 80}))
                        [(asset
                          "CORP"
                          "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
            [(weight-equal
              [(if
                (>
                 (cumulative-return "LQD" {:window 70})
                 (cumulative-return "CORP" {:window 65}))
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "LQD" {:window 80})
                     (cumulative-return "CORP" {:window 80}))
                    [(asset
                      "CORP"
                      "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                    [(asset
                      "BIL"
                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                [(asset
                  "BIL"
                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])]))
