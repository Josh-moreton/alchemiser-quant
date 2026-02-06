;; Filterable Group: YINN YANG Mean Reversion [FTL Copy] w/ WAM Updated Package
;; Extracted from: ftl_starburst.clj
;; Parent Group: WYLD Mean Reversion Combo v2 w/ Overcompensating Frontrunner [FTL]
;; Used by filter: (moving-average-return {:window 10}) (select-bottom 1)
;; Required lookback: 10 days for filter scoring
(defsymphony
 "YINN YANG Mean Reversion [FTL Copy]"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "YINN YANG Mean Reversion [FTL Copy] w/ WAM Updated Package"
    [(weight-equal
      [(if
        (> (cumulative-return "FXI" {:window 5}) 10)
        [(group
          "Bullish Mean Reversion"
          [(weight-equal
            [(if
              (< (cumulative-return "FXI" {:window 1}) -2)
              [(asset "YINN" "Direxion Daily FTSE China Bull 3X Shares")]
              [(asset "YANG" "Direxion Daily FTSE China Bear 3X Shares")])])])]
        [(group
          "Bearish Mean Reversion"
          [(weight-equal
            [(if
              (< (cumulative-return "FXI" {:window 5}) -10)
              [(weight-equal
                [(if
                  (> (cumulative-return "FXI" {:window 1}) 2)
                  [(asset "YANG" "Direxion Daily FTSE China Bear 3X Shares")]
                  [(asset "YINN" "Direxion Daily FTSE China Bull 3X Shares")])])]
              [(group
                "07/24/2024 Overcompensating Frontrunner v2"
                [(weight-equal
                  [(if
                    (> (rsi "IEF" {:window 20}) (rsi "PSQ" {:window 60}))
                    [(weight-equal
                      [(filter
                        (stdev-return {:window 12})
                        (select-top 1)
                        [(group "MAX DD: TQQQ vs UVXY"
                          [(weight-equal
                            [(filter (max-drawdown {:window 11}) (select-bottom 1)
                              [(asset "TQQQ" "ProShares UltraPro QQQ")
                               (asset "UVXY" "ProShares Ultra VIX Short-Term Futures ETF")])])])
                         (group "MAX DD: TQQQ vs SOXL"
                          [(weight-equal
                            [(filter (max-drawdown {:window 10}) (select-bottom 1)
                              [(asset "TQQQ" "ProShares UltraPro QQQ")
                               (asset "SOXL" "Direxion Daily Semiconductor Bull 3x Shares")])])])
                         (group "MAX DD: TQQQ vs FNGU"
                          [(weight-equal
                            [(filter (max-drawdown {:window 9}) (select-bottom 1)
                              [(asset "TQQQ" "ProShares UltraPro QQQ")
                               (asset "FNGU" "MicroSectors FANG+ Index 3X Leveraged ETN")])])])
                         (group "MAX DD: TQQQ vs UUP"
                          [(weight-equal
                            [(filter (max-drawdown {:window 10}) (select-bottom 1)
                              [(asset "TQQQ" "ProShares UltraPro QQQ")
                               (asset "UUP" "Invesco DB US Dollar Index Bullish Fund")])])])
                         (group "MAX DD: TQQQ vs VDE"
                          [(weight-equal
                            [(filter (max-drawdown {:window 10}) (select-bottom 1)
                              [(asset "TQQQ" "ProShares UltraPro QQQ")
                               (asset "VDE" "Vanguard Energy ETF")])])])
                         (group "MAX DD: TQQQ vs SMH"
                          [(weight-equal
                            [(filter (max-drawdown {:window 11}) (select-bottom 1)
                              [(asset "TQQQ" "ProShares UltraPro QQQ")
                               (asset "SMH" "VanEck Semiconductor ETF")])])])
                         (group "MAX DD: TQQQ vs AVUV"
                          [(weight-equal
                            [(filter (max-drawdown {:window 12}) (select-bottom 1)
                              [(asset "TQQQ" "ProShares UltraPro QQQ")
                               (asset "AVUV" "Avantis U.S. Small Cap Value ETF")])])])
                         (group "MAX DD: TQQQ vs NAIL"
                          [(weight-equal
                            [(filter (max-drawdown {:window 12}) (select-bottom 1)
                              [(asset "TQQQ" "ProShares UltraPro QQQ")
                               (asset "NAIL" "Direxion Daily Homebuilders & Supplies Bull 3X Shares")])])])])])]
                    [(group
                      "WAM Updated Package | New & Improved WAM + WAM V2 WHS + WAM V3"
                      [(weight-equal
                        [(group "New & Improved WAM"
                          [(weight-equal
                            [(if (> (rsi "VIXM" {:window 14}) 70)
                              [(weight-equal [(asset "BIL" "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                              [(weight-equal
                                [(filter
                                  (moving-average-return {:window 5})
                                  (select-top 1)
                                  [(group "Muted WAMCore"
                                    [(weight-equal
                                      [(if (> (rsi "AGG" {:window 15}) (rsi "QQQ" {:window 15}))
                                        [(weight-equal
                                          [(group "Muted Bull"
                                            [(weight-equal
                                              [(filter (moving-average-return {:window 4}) (select-bottom 3)
                                                [(asset "XLK" "Technology Select Sector SPDR Fund")
                                                 (asset "QQQ" "Invesco QQQ Trust Series I")
                                                 (asset "XLRE" "Real Estate Select Sector SPDR Fund")
                                                 (asset "IWM" "iShares Russell 2000 ETF")
                                                 (asset "SOXX" "iShares Semiconductor ETF")
                                                 (asset "EEM" "iShares MSCI Emerging Markets ETF")])])])])]
                                        [(weight-equal
                                          [(group "Muted Bear"
                                            [(weight-equal
                                              [(filter (moving-average-return {:window 4}) (select-bottom 3)
                                                [(asset "PSQ" "ProShares Short QQQ")
                                                 (asset "DOG" "ProShares Short Dow30")
                                                 (asset "SH" "ProShares Short S&P500")
                                                 (asset "RWM" "ProShares Short Russell2000")
                                                 (asset "TBF" "Proshares Short 20+ Year Treasury")])])])])])])])
                                   (group "WAMCore"
                                    [(weight-equal
                                      [(if (> (rsi "AGG" {:window 15}) (rsi "QQQ" {:window 15}))
                                        [(weight-equal
                                          [(group "Bull"
                                            [(weight-equal
                                              [(filter (moving-average-return {:window 4}) (select-bottom 2)
                                                [(asset "TECL" "Direxion Daily Technology Bull 3x Shares")
                                                 (asset "TQQQ" "ProShares UltraPro QQQ")
                                                 (asset "DRN" "Direxion Daily Real Estate Bull 3x Shares")
                                                 (asset "URTY" "ProShares UltraPro Russell2000")
                                                 (asset "SOXL" "Direxion Daily Semiconductor Bull 3x Shares")
                                                 (asset "EDC" "Direxion Daily MSCI Emerging Markets Bull 3x Shares")])])])])]
                                        [(weight-equal
                                          [(group "Bear"
                                            [(weight-equal
                                              [(filter (moving-average-return {:window 4}) (select-bottom 3)
                                                [(asset "TECS" "Direxion Daily Technology Bear 3X Shares")
                                                 (asset "SQQQ" "ProShares UltraPro Short QQQ")
                                                 (asset "DRV" "Direxion Daily Real Estate Bear 3X Shares")
                                                 (asset "SRTY" "ProShares UltraPro Short Russell2000")
                                                 (asset "TMV" "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])
                                   (asset "QQQ" "Invesco QQQ Trust Series I")])])])])])
                         (group "WAM V2 | WHS"
                          [(weight-equal
                            [(if (< (rsi "XLE" {:window 20}) (rsi "XLK" {:window 20}))
                              [(asset "QQQ" nil)]
                              [(group "WAM Rotator | WHS"
                                [(weight-equal
                                  [(filter (moving-average-return {:window 5}) (select-top 1)
                                    [(group "Muted WAMCore"
                                      [(weight-equal
                                        [(if (> (rsi "AGG" {:window 15}) (rsi "QQQ" {:window 15}))
                                          [(group "Muted Bull"
                                            [(weight-equal
                                              [(filter (moving-average-return {:window 4}) (select-bottom 3)
                                                [(asset "XLK" nil) (asset "QQQ" nil) (asset "XLRE" nil)
                                                 (asset "IWM" nil) (asset "SOXX" nil) (asset "EEM" nil)])])])]
                                          [(group "Muted Bear"
                                            [(weight-equal
                                              [(filter (moving-average-return {:window 4}) (select-bottom 3)
                                                [(asset "SH" nil) (asset "PSQ" nil) (asset "DOG" nil)
                                                 (asset "RWM" nil) (asset "TBF" nil)])])])])])])
                                     (group "WAMCore"
                                      [(weight-equal
                                        [(if (> (rsi "AGG" {:window 15}) (rsi "QQQ" {:window 15}))
                                          [(group "Bull"
                                            [(weight-equal
                                              [(filter (moving-average-return {:window 4}) (select-bottom 2)
                                                [(asset "TECL" nil) (asset "TQQQ" nil) (asset "DRN" nil)
                                                 (asset "URTY" nil) (asset "SOXL" nil) (asset "EDC" nil)])])])]
                                          [(group "Bear"
                                            [(weight-equal
                                              [(filter (moving-average-return {:window 4}) (select-bottom 3)
                                                [(asset "TECS" nil) (asset "SQQQ" nil) (asset "DRV" nil)
                                                 (asset "SRTY" nil) (asset "TMV" nil)])])])])])])])])])])])])
                         (group "WAM V3"
                          [(weight-equal
                            [(if (< (rsi "QQQ" {:window 10}) 30)
                              [(asset "TQQQ" nil)]
                              [(weight-equal
                                [(if (> (rsi "XLE" {:window 15}) (rsi "XLK" {:window 15}))
                                  [(weight-equal
                                    [(if (> (rsi "AGG" {:window 15}) (rsi "QQQ" {:window 15}))
                                      [(group "Bull"
                                        [(weight-equal
                                          [(filter (cumulative-return {:window 5}) (select-bottom 3)
                                            [(asset "TQQQ" nil) (asset "TECL" nil) (asset "URTY" nil)
                                             (asset "DRN" nil) (asset "TMF" nil)])])])]
                                      [(group "Bear"
                                        [(weight-equal
                                          [(filter (cumulative-return {:window 5}) (select-bottom 3)
                                            [(asset "SQQQ" nil) (asset "TECS" nil) (asset "SRTY" nil)
                                             (asset "DRV" nil) (asset "TMV" nil)])])])])])]
                                  [(group "Alternate"
                                    [(weight-equal
                                      [(filter (cumulative-return {:window 20}) (select-top 2)
                                        [(asset "TQQQ" nil) (asset "UPRO" nil) (asset "URTY" nil) (asset "QQQ" nil)])])])])])])])])])])])])])])])])])
