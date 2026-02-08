;; Filterable Group: MAX DD: TQQQ vs SMH
;; Extracted from: ftl_starburst.clj
;; Parent Group: 07/24/2024 Overcompensating Frontrunner v2
;; Used by filter: (stdev-return {:window 12}) (select-top 1)
;; Required lookback: 12 days for filter scoring
(defsymphony
 "MAX DD: TQQQ vs SMH"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "MAX DD: TQQQ vs SMH"
    [(weight-equal
      [(filter
        (max-drawdown {:window 11})
        (select-bottom 1)
        [(asset "TQQQ" "ProShares UltraPro QQQ")
         (asset "SMH" "VanEck Semiconductor ETF")])])])]))
