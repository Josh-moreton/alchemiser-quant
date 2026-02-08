;; Filterable Group: Overcompensating Frontrunner v2
;; Extracted from: ftl_starburst.clj
;; Parent Group: YINN YANG / LABU LABD / DRV DRN Mean Reversion (shared)
;; Used by filter: (moving-average-return {:window 10}) (select-bottom 1) [top-level]
;; Inner filter: (stdev-return {:window 12}) (select-top 1) on 8 MAX DD sub-groups
;; Required lookback: 12 days for filter scoring
(defsymphony
 "Overcompensating Frontrunner v2"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "07/24/2024 Overcompensating Frontrunner v2"
    [(weight-equal
      [(filter
        (stdev-return {:window 12})
        (select-top 1)
        [(group
          "MAX DD: TQQQ vs UVXY"
          [(weight-equal
            [(filter
              (max-drawdown {:window 11})
              (select-bottom 1)
              [(asset "TQQQ" "ProShares UltraPro QQQ")
               (asset "UVXY" "ProShares Ultra VIX Short-Term Futures ETF")])])])
         (group
          "MAX DD: TQQQ vs SOXL"
          [(weight-equal
            [(filter
              (max-drawdown {:window 10})
              (select-bottom 1)
              [(asset "TQQQ" "ProShares UltraPro QQQ")
               (asset "SOXL" "Direxion Daily Semiconductor Bull 3x Shares")])])])
         (group
          "MAX DD: TQQQ vs FNGU"
          [(weight-equal
            [(filter
              (max-drawdown {:window 9})
              (select-bottom 1)
              [(asset "TQQQ" "ProShares UltraPro QQQ")
               (asset "FNGU" "MicroSectors FANG+ Index 3X Leveraged ETN")])])])
         (group
          "MAX DD: TQQQ vs UUP"
          [(weight-equal
            [(filter
              (max-drawdown {:window 10})
              (select-bottom 1)
              [(asset "TQQQ" "ProShares UltraPro QQQ")
               (asset "UUP" "Invesco DB US Dollar Index Bullish Fund")])])])
         (group
          "MAX DD: TQQQ vs VDE"
          [(weight-equal
            [(filter
              (max-drawdown {:window 10})
              (select-bottom 1)
              [(asset "TQQQ" "ProShares UltraPro QQQ")
               (asset "VDE" "Vanguard Energy ETF")])])])
         (group
          "MAX DD: TQQQ vs SMH"
          [(weight-equal
            [(filter
              (max-drawdown {:window 11})
              (select-bottom 1)
              [(asset "TQQQ" "ProShares UltraPro QQQ")
               (asset "SMH" "VanEck Semiconductor ETF")])])])
         (group
          "MAX DD: TQQQ vs AVUV"
          [(weight-equal
            [(filter
              (max-drawdown {:window 12})
              (select-bottom 1)
              [(asset "TQQQ" "ProShares UltraPro QQQ")
               (asset "AVUV" "Avantis U.S. Small Cap Value ETF")])])])
         (group
          "MAX DD: TQQQ vs NAIL"
          [(weight-equal
            [(filter
              (max-drawdown {:window 12})
              (select-bottom 1)
              [(asset "TQQQ" "ProShares UltraPro QQQ")
               (asset "NAIL" "Direxion Daily Homebuilders & Supplies Bull 3X Shares")])])])])])])]))
