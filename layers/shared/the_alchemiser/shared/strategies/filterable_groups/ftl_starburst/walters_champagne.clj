;; Filterable Group: Walter's Champagne and CocaineStrategies
;; Extracted from: ftl_starburst.clj
;; Parent Strategy: FTL Starburst | Interstellar Mods
;; Used by filters: (moving-average-return {:window 10}), (rsi {:window 10}), (stdev-return {:window 10})
;; Required lookback: 10 days for filter scoring
(defsymphony
 " Walter's Champagne and CocaineStrategies"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    " Walter's Champagne and CocaineStrategies"
    [(weight-equal
      [(group
        "KMLM | Technology"
        [(weight-equal
          [(if
            (>
             (rsi "XLK" {:window 10})
             (rsi "KMLM" {:window 10}))
            [(asset
              "TECL"
              "Direxion Daily Technology Bull 3x Shares")]
            [(asset
              "TECS"
              "Direxion Daily Technology Bear 3X Shares")])])])
       (group
        "Modified Foreign Rat"
        [(weight-equal
          [(if
            (>
             (current-price "EEM")
             (moving-average-price "EEM" {:window 200}))
            [(weight-equal
              [(if
                (>
                 (rsi "IEI" {:window 11})
                 (rsi "IWM" {:window 16}))
                [(asset
                  "EDC"
                  "Direxion Daily MSCI Emerging Markets Bull 3x Shares")]
                [(asset
                  "EDZ"
                  "Direxion Daily MSCI Emerging Markets Bear 3X Shares")])])]
            [(weight-equal
              [(if
                (>
                 (rsi "IEI" {:window 11})
                 (rsi "EEM" {:window 16}))
                [(asset
                  "EDC"
                  "Direxion Daily MSCI Emerging Markets Bull 3x Shares")]
                [(asset
                  "EDZ"
                  "Direxion Daily MSCI Emerging Markets Bear 3X Shares")])])])])])
       (group
        "JRT"
        [(weight-inverse-volatility
          10
          [(asset "LLY" nil)
           (asset "NVO" nil)
           (asset "COST" nil)
           (group
            "PGR || GE"
            [(weight-equal
              [(filter
                (moving-average-return {:window 60})
                (select-top 1)
                [(asset "PGR" nil) (asset "GE" nil)])])])])])])])]))
