;; Filterable Group: WAMCore
;; Extracted from: ftl_starburst.clj
;; Parent Group: New & Improved WAM / WAM Rotator | WHS
;; Used by filter: (moving-average-return {:window 5}) (select-top 1)
;; Required lookback: 5 days for filter scoring
;; Inner logic: RSI gate AGG(15) > QQQ(15) switches bull/bear
;; Bull: 3x leveraged ETFs (TECL, TQQQ, DRN, URTY, SOXL, EDC) select-bottom 2
;; Bear: 3x inverse ETFs (TECS, SQQQ, DRV, SRTY, TMV) select-bottom 3
(defsymphony
 "WAMCore"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "WAMCore"
    [(weight-equal
      [(if
        (> (rsi "AGG" {:window 15}) (rsi "QQQ" {:window 15}))
        [(weight-equal
          [(group
            "Bull"
            [(weight-equal
              [(filter
                (moving-average-return {:window 4})
                (select-bottom 2)
                [(asset "TECL" "Direxion Daily Technology Bull 3x Shares")
                 (asset "TQQQ" "ProShares UltraPro QQQ")
                 (asset "DRN" "Direxion Daily Real Estate Bull 3x Shares")
                 (asset "URTY" "ProShares UltraPro Russell2000")
                 (asset "SOXL" "Direxion Daily Semiconductor Bull 3x Shares")
                 (asset "EDC" "Direxion Daily MSCI Emerging Markets Bull 3x Shares")])])])])]
        [(weight-equal
          [(group
            "Bear"
            [(weight-equal
              [(filter
                (moving-average-return {:window 4})
                (select-bottom 3)
                [(asset "TECS" "Direxion Daily Technology Bear 3X Shares")
                 (asset "SQQQ" "ProShares UltraPro Short QQQ")
                 (asset "DRV" "Direxion Daily Real Estate Bear 3X Shares")
                 (asset "SRTY" "ProShares UltraPro Short Russell2000")
                 (asset "TMV" "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])]))
