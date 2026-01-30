(defsymphony
 "Gold Currency Hedge"
 {:asset-class "EQUITIES", :rebalance-threshold 0.1}
 (weight-equal
  [(if
    (< (rsi "GLD" {:window 10}) 30)
    [(asset "SHNY" "MicroSectors Gold 3X Leveraged ETNs")]
    [(weight-equal
      [(if
        (> (cumulative-return "GLD" {:window 10}) 1)
        [(asset "SHNY" "MicroSectors Gold 3X Leveraged ETNs")]
        [(asset "GLD" "SPDR Gold Shares")])])])]))
