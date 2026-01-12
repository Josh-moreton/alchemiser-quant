(defsymphony
 "Algo 1.2 Gold"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-specified
  1
  (if
   (> (rsi "GDXU" {:window 10}) 79)
   [(asset
     "GDXD"
     "Bank of Montreal - MicroSectors Gold Miners -3X Inverse Leveraged ETNs")]
   [(weight-equal
     [(if
       (< (rsi "GDXU" {:window 10}) 30)
       [(asset
         "GDXU"
         "Bank of Montreal - MicroSectors Gold Miners 3X Leveraged ETN")]
       [(weight-equal
         [(if
           (>
            (cumulative-return "QQQ" {:window 90})
            (cumulative-return "QQQ" {:window 70}))
           [(weight-equal
             [(if
               (<
                (cumulative-return "GDXU" {:window 70})
                (cumulative-return "GDXU" {:window 75}))
               [(asset
                 "GDXU"
                 "Bank of Montreal - MicroSectors Gold Miners 3X Leveraged ETN")]
               [(asset
                 "BIL"
                 "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
           [(weight-equal
             [(if
               (<
                (cumulative-return "TLT" {:window 95})
                (cumulative-return "QQQ" {:window 35}))
               [(asset
                 "GDXD"
                 "Bank of Montreal - MicroSectors Gold Miners -3X Inverse Leveraged ETNs")]
               [(asset
                 "BIL"
                 "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])))
