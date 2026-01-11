(defsymphony
 "Group \"Stuff"
 {:asset-class "EQUITIES", :rebalance-frequency :quarterly}
 (weight-specified
  0.3
  (group
   "Stuff I Like"
   [(weight-equal
     [(asset "SOFI" "SoFi Technologies Inc")
      (filter
       (rsi {:window 20})
       (select-bottom 1)
       [(asset "ACHR" "Archer Aviation Inc Class A")
        (asset "SGOV" "iShares 0-3 Month Treasury Bond ETF")])
      (asset "HIMS" "Hims & Hers Health, Inc. Class A")
      (filter
       (rsi {:window 20})
       (select-bottom 1)
       [(asset "MARA" "MARA Holdings, Inc.")
        (asset "UVIX" "2x Long VIX Futures ETF")])
      (filter
       (rsi {:window 14})
       (select-bottom 1)
       [(asset "FAS" "Direxion Daily Financial Bull 3x Shares")
        (asset "UVIX" "2x Long VIX Futures ETF")])
      (filter
       (rsi {:window 14})
       (select-top 1)
       [(asset "SMCX" "Defiance Daily Target 2X Long SMCI ETF")
        (asset "SGOV" "iShares 0-3 Month Treasury Bond ETF")])])])
  0.7
  (group
   "Rigged"
   [(weight-equal [(asset "RGTI" "Rigetti Computing, Inc.")])])))
