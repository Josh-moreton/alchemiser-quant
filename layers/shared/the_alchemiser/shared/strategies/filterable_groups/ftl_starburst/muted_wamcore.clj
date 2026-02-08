;; Filterable Group: Muted WAMCore
;; Extracted from: ftl_starburst.clj
;; Parent Group: New & Improved WAM / WAM Rotator | WHS
;; Used by filter: (moving-average-return {:window 5}) (select-top 1)
;; Required lookback: 5 days for filter scoring
;; Inner logic: RSI gate AGG(15) > QQQ(15) switches bull/bear
;; Bull: 1x ETFs (XLK, QQQ, XLRE, IWM, SOXX, EEM) select-bottom 3
;; Bear: 1x inverse ETFs (PSQ, DOG, SH, RWM, TBF) select-bottom 3
(defsymphony
 "Muted WAMCore"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "Muted WAMCore"
    [(weight-equal
      [(if
        (> (rsi "AGG" {:window 15}) (rsi "QQQ" {:window 15}))
        [(weight-equal
          [(group
            "Muted Bull"
            [(weight-equal
              [(filter
                (moving-average-return {:window 4})
                (select-bottom 3)
                [(asset "XLK" "Technology Select Sector SPDR Fund")
                 (asset "QQQ" "Invesco QQQ Trust Series I")
                 (asset "XLRE" "Real Estate Select Sector SPDR Fund")
                 (asset "IWM" "iShares Russell 2000 ETF")
                 (asset "SOXX" "iShares Semiconductor ETF")
                 (asset "EEM" "iShares MSCI Emerging Markets ETF")])])])])]
        [(weight-equal
          [(group
            "Muted Bear"
            [(weight-equal
              [(filter
                (moving-average-return {:window 4})
                (select-bottom 3)
                [(asset "PSQ" "ProShares Short QQQ")
                 (asset "DOG" "ProShares Short Dow30")
                 (asset "SH" "ProShares Short S&P500")
                 (asset "RWM" "ProShares Short Russell2000")
                 (asset "TBF" "Proshares Short 20+ Year Treasury")])])])])])])])]))
