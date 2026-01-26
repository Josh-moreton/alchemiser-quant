(defsymphony
 "Blatant Tech Rulership"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
    (< (rsi "GDX" {:window 7}) 70)
    [(group
      "Metals"
      [(weight-equal
        [(if
          (> (rsi "GDX" {:window 7}) 40)
          [(weight-equal
            [(filter
              (rsi {:window 10})
              (select-top 2)
              [(asset
                "CPXR"
                "Tidal Trust III - USCF Daily Target 2X Copper Index ETF")
               (asset
                "AGQ"
                "ProShares Trust - ProShares Ultra Silver 2x Shares")
               (asset
                "GDXU"
                "Bank of Montreal - MicroSectors Gold Miners 3X Leveraged ETN")])])]
          [(weight-equal
            [(filter
              (rsi {:window 10})
              (select-top 1)
              [(asset
                "NBIS"
                "Nebius Group N.V. - Ordinary Shares - Class A")
               (asset "APLD" "Applied Digital Corporation")
               (asset
                "BE"
                "Bloom Energy Corp - Ordinary Shares - Class A")])])])])])]
    [(asset
      "CORD"
      "ETF Opportunities Trust - T-REX 2X Inverse CRWV Daily Target ETF")])
   (if
    (< (rsi "CRWV" {:window 10}) 80)
    [(weight-equal
      [(if
        (> (rsi "CRWV" {:window 10}) 30)
        [(weight-equal
          [(filter
            (rsi {:window 10})
            (select-bottom 1)
            [(asset
              "NBIS"
              "Nebius Group N.V. - Ordinary Shares - Class A")
             (asset "APLD" "Applied Digital Corporation")
             (asset
              "BE"
              "Bloom Energy Corp - Ordinary Shares - Class A")])])]
        [(group
          "Metals"
          [(weight-equal
            [(asset
              "CORD"
              "ETF Opportunities Trust - T-REX 2X Inverse CRWV Daily Target ETF")
             (if
              (> (rsi "GDX" {:window 7}) 40)
              [(weight-equal
                [(filter
                  (rsi {:window 10})
                  (select-top 2)
                  [(asset
                    "CPXR"
                    "Tidal Trust III - USCF Daily Target 2X Copper Index ETF")
                   (asset
                    "AGQ"
                    "ProShares Trust - ProShares Ultra Silver 2x Shares")
                   (asset
                    "GDXU"
                    "Bank of Montreal - MicroSectors Gold Miners 3X Leveraged ETN")])])]
              [(weight-equal
                [(filter
                  (rsi {:window 10})
                  (select-top 1)
                  [(asset
                    "NBIS"
                    "Nebius Group N.V. - Ordinary Shares - Class A")
                   (asset "APLD" "Applied Digital Corporation")
                   (asset
                    "BE"
                    "Bloom Energy Corp - Ordinary Shares - Class A")])])])])])])])]
    [(asset
      "CORD"
      "ETF Opportunities Trust - T-REX 2X Inverse CRWV Daily Target ETF")])
   (weight-equal
    [(if
      (>= (max-drawdown "SOXL" {:window 60}) 50)
      [(weight-equal
        [(if
          (<= (stdev-return "TQQQ" {:window 14}) 18)
          [(weight-equal
            [(if
              (<= (stdev-return "TQQQ" {:window 100}) 3.8)
              [(weight-equal
                [(filter
                  (cumulative-return {:window 21})
                  (select-top 2)
                  [(asset
                    "SOXL"
                    "Direxion Daily Semiconductor Bull 3x Shares")
                   (asset "TQQQ" "ProShares UltraPro QQQ")
                   (asset
                    "SPXL"
                    "Direxion Daily S&P 500 Bull 3x Shares")])])]
              [(weight-equal
                [(if
                  (>= (rsi "TQQQ" {:window 30}) 50)
                  [(weight-equal
                    [(if
                      (>= (stdev-return "TQQQ" {:window 30}) 5.8)
                      [(asset
                        "SOXS"
                        "Direxion Daily Semiconductor Bear 3x Shares")]
                      [(asset
                        "SPXL"
                        "Direxion Daily S&P 500 Bull 3x Shares")])])]
                  [(weight-equal
                    [(if
                      (<= (cumulative-return "TQQQ" {:window 8}) -20)
                      [(asset
                        "SOXL"
                        "Direxion Daily Semiconductor Bull 3x Shares")]
                      [(weight-equal
                        [(if
                          (<= (max-drawdown "TQQQ" {:window 200}) 65)
                          [(weight-equal
                            [(filter
                              (cumulative-return {:window 3})
                              (select-bottom 2)
                              [(asset
                                "TMV"
                                "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                               (asset
                                "SQQQ"
                                "ProShares UltraPro Short QQQ")
                               (asset
                                "SPXS"
                                "Direxion Daily S&P 500 Bear 3x Shares")
                               (asset
                                "SPXS"
                                "Direxion Daily S&P 500 Bear 3x Shares")])])]
                          [(asset
                            "SOXL"
                            "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])]
          [(weight-equal
            [(if
              (<= (cumulative-return "TQQQ" {:window 30}) -10)
              [(weight-equal
                [(filter
                  (cumulative-return {:window 3})
                  (select-bottom 2)
                  [(asset
                    "TMV"
                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                   (asset "SQQQ" "ProShares UltraPro Short QQQ")
                   (asset
                    "SPXS"
                    "Direxion Daily S&P 500 Bear 3x Shares")
                   (asset
                    "SPXS"
                    "Direxion Daily S&P 500 Bear 3x Shares")])])]
              [(weight-equal
                [(filter
                  (cumulative-return {:window 21})
                  (select-top 3)
                  [(asset
                    "SOXL"
                    "Direxion Daily Semiconductor Bull 3x Shares")
                   (asset "TQQQ" "ProShares UltraPro QQQ")
                   (asset
                    "TMF"
                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                   (asset
                    "SPXL"
                    "Direxion Daily S&P 500 Bull 3x Shares")])])])])])])]
      [(weight-equal
        [(if
          (<= (rsi "SOXL" {:window 32}) 62.1995)
          [(weight-equal
            [(if
              (<= (stdev-return "SOXL" {:window 105}) 4.9226)
              [(asset
                "SOXL"
                "Direxion Daily Semiconductor Bull 3x Shares")]
              [(weight-equal
                [(if
                  (>= (rsi "SOXL" {:window 30}) 57.49)
                  [(weight-equal
                    [(if
                      (>= (stdev-return "SOXL" {:window 30}) 5.4135)
                      [(asset
                        "SOXS"
                        "Direxion Daily Semiconductor Bear 3x Shares")]
                      [(weight-equal
                        [(filter
                          (cumulative-return {:window 21})
                          (select-top 2)
                          [(asset
                            "SOXL"
                            "Direxion Daily Semiconductor Bull 3x Shares")
                           (asset
                            "SPXL"
                            "Direxion Daily S&P 500 Bull 3x Shares")
                           (asset
                            "TQQQ"
                            "ProShares UltraPro QQQ")])])])])]
                  [(weight-equal
                    [(if
                      (<= (cumulative-return "SOXL" {:window 32}) -12)
                      [(asset
                        "SOXL"
                        "Direxion Daily Semiconductor Bull 3x Shares")]
                      [(weight-equal
                        [(if
                          (<= (max-drawdown "SOXL" {:window 250}) 71)
                          [(asset
                            "SOXS"
                            "Direxion Daily Semiconductor Bear 3x Shares")]
                          [(asset
                            "SOXL"
                            "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])]
          [(weight-equal
            [(if
              (>= (rsi "SOXL" {:window 32}) 50)
              [(asset
                "SOXS"
                "Direxion Daily Semiconductor Bear 3x Shares")]
              [(weight-equal
                [(filter
                  (cumulative-return {:window 21})
                  (select-top 3)
                  [(asset
                    "SOXL"
                    "Direxion Daily Semiconductor Bull 3x Shares")
                   (asset "TQQQ" "ProShares UltraPro QQQ")
                   (asset
                    "TMF"
                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                   (asset
                    "SPXL"
                    "Direxion Daily S&P 500 Bull 3x Shares")])])])])])])])])]))
