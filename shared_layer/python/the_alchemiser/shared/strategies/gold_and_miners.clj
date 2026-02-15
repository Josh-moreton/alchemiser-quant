(defsymphony
 "Gold and Miner Friendship - Structural Filter"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
    (<
     (cumulative-return "GDX" {:window 35})
     (cumulative-return "GLD" {:window 35}))
    [(weight-equal
      [(if
        (<
         (cumulative-return "GLD" {:window 35})
         (cumulative-return "SPY" {:window 35}))
        [(asset "SPY" nil)]
        [(asset "BIL" nil)])])]
    [(if
      (< (cumulative-return "GDX" {:window 20}) -2)
      [(asset "BIL" nil)]
      [(if
        (> (rsi "GDXU" {:window 10}) 79)
        [(asset
          "GDXD"
          "Bank of Montreal - MicroSectors Gold Miners -3X Inverse Leveraged ETNs")
         (weight-equal
          [(if
            (> (rsi "SHNY" {:window 10}) 79)
            [(asset
              "DULL"
              "Bank of Montreal - MicroSectors Gold -3X Inverse Leveraged ETNs")]
            [(asset
              "GDXD"
              "Bank of Montreal - MicroSectors Gold Miners -3X Inverse Leveraged ETNs")])])]
        [(weight-equal
          [(if
            (> (rsi "SHNY" {:window 10}) 79)
            [(asset
              "DULL"
              "Bank of Montreal - MicroSectors Gold -3X Inverse Leveraged ETNs")]
            [(weight-equal
              [(if
                (< (rsi "GDXU" {:window 10}) 30)
                [(asset
                  "GDXU"
                  "Bank of Montreal - MicroSectors Gold Miners 3X Leveraged ETN")
                 (weight-equal
                  [(if
                    (< (rsi "SHNY" {:window 10}) 30)
                    [(asset
                      "SHNY"
                      "Bank of Montreal - MicroSectors Gold 3X Leveraged ETNs")]
                    [(asset
                      "GDXU"
                      "Bank of Montreal - MicroSectors Gold Miners 3X Leveraged ETN")])])]
                [(weight-equal
                  [(if
                    (< (rsi "SHNY" {:window 10}) 30)
                    [(asset
                      "SHNY"
                      "Bank of Montreal - MicroSectors Gold 3X Leveraged ETNs")]
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
                              "Bank of Montreal - MicroSectors Gold Miners 3X Leveraged ETN")
                             (weight-equal
                              [(if
                                (<
                                 (cumulative-return
                                  "SHNY"
                                  {:window 70})
                                 (cumulative-return
                                  "SHNY"
                                  {:window 75}))
                                [(asset
                                  "SHNY"
                                  "Bank of Montreal - MicroSectors Gold 3X Leveraged ETNs")]
                                [(asset
                                  "GDXU"
                                  "Bank of Montreal - MicroSectors Gold Miners 3X Leveraged ETN")])])]
                            [(weight-equal
                              [(if
                                (<
                                 (cumulative-return
                                  "SHNY"
                                  {:window 70})
                                 (cumulative-return
                                  "SHNY"
                                  {:window 75}))
                                [(asset
                                  "SHNY"
                                  "Bank of Montreal - MicroSectors Gold 3X Leveraged ETNs")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (<
                             (cumulative-return "TLT" {:window 95})
                             (cumulative-return "QQQ" {:window 35}))
                            [(asset
                              "GDXD"
                              "Bank of Montreal - MicroSectors Gold Miners -3X Inverse Leveraged ETNs")
                             (asset
                              "DULL"
                              "Bank of Montreal - MicroSectors Gold -3X Inverse Leveraged ETNs")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])]))
