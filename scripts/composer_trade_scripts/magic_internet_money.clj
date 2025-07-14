(defsymphony
 "V1a Magic Internet Money (Base 2 - FTLT)"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "V1a Magic Internet Money (Base 2 - FTLT)"
    [(weight-equal
      [(if
        (<=
         (current-price "BITO")
         (moving-average-price "BITO" {:window 62}))
        [(weight-equal
          [(if
            (> (rsi "BITO" {:window 14}) 60)
            [(asset "BITI" "ProShares Short Bitcoin Strategy ETF")]
            [(weight-equal
              [(if
                (<= (cumulative-return "BITI" {:window 1}) -1)
                [(weight-equal
                  [(if
                    (<= (cumulative-return "BITO" {:window 1}) -2)
                    [(asset
                      "BIL"
                      "SPDR Bloomberg 1-3 Month T-Bill ETF")]
                    [(asset
                      "MSTR"
                      "MicroStrategy Incorporated Class A")])])]
                [(weight-equal
                  [(if
                    (>=
                     (cumulative-return "BITO" {:window 5})
                     (stdev-return "BITO" {:window 10}))
                    [(asset
                      "BITI"
                      "ProShares Short Bitcoin Strategy ETF")]
                    [(weight-equal
                      [(if
                        (>=
                         (cumulative-return "BITO" {:window 2})
                         (stdev-return "BITO" {:window 5}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "BITO" {:window 1})
                             (cumulative-return "BITI" {:window 3}))
                            [(asset
                              "MSTR"
                              "MicroStrategy Incorporated Class A")]
                            [(weight-equal
                              [(group
                                "Base 2 - FTLT or Bull or Bonds (UVXY)"
                                [(weight-equal
                                  [(if
                                    (> (rsi "QQQE" {:window 10}) 79)
                                    [(asset
                                      "UVXY"
                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                    [(weight-equal
                                      [(if
                                        (> (rsi "VTV" {:window 10}) 79)
                                        [(asset
                                          "UVXY"
                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "VOX" {:window 10})
                                             79)
                                            [(asset
                                              "UVXY"
                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "TECL"
                                                  {:window 10})
                                                 79)
                                                [(asset
                                                  "UVXY"
                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "VOOG"
                                                      {:window 10})
                                                     79)
                                                    [(asset
                                                      "UVXY"
                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VOOV"
                                                          {:window 10})
                                                         79)
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "XLP"
                                                              {:window
                                                               10})
                                                             75)
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "TQQQ"
                                                                  {:window
                                                                   10})
                                                                 79)
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UVXY"
                                                                    "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "XLY"
                                                                      {:window
                                                                       10})
                                                                     80)
                                                                    [(asset
                                                                      "UVXY"
                                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "FAS"
                                                                          {:window
                                                                           10})
                                                                         80)
                                                                        [(asset
                                                                          "UVXY"
                                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "SPY"
                                                                              {:window
                                                                               10})
                                                                             80)
                                                                            [(asset
                                                                              "UVXY"
                                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                            [(weight-equal
                                                                              [(if
                                                                                (<
                                                                                 (cumulative-return
                                                                                  "TQQQ"
                                                                                  {:window
                                                                                   6})
                                                                                 -12)
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (>
                                                                                     (cumulative-return
                                                                                      "TQQQ"
                                                                                      {:window
                                                                                       1})
                                                                                     5.5)
                                                                                    [(weight-equal
                                                                                      [(asset
                                                                                        "UVXY"
                                                                                        "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                    [(weight-equal
                                                                                      [(group
                                                                                        "FTLT or Safety Town"
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (<
                                                                                             (rsi
                                                                                              "TQQQ"
                                                                                              {:window
                                                                                               10})
                                                                                             30)
                                                                                            [(asset
                                                                                              "TECL"
                                                                                              "Direxion Daily Technology Bull 3x Shares")]
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (<
                                                                                                 (rsi
                                                                                                  "SOXL"
                                                                                                  {:window
                                                                                                   10})
                                                                                                 30)
                                                                                                [(asset
                                                                                                  "SOXL"
                                                                                                  "Direxion Daily Semiconductor Bull 3x Shares")]
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (<
                                                                                                     (rsi
                                                                                                      "SPXL"
                                                                                                      {:window
                                                                                                       10})
                                                                                                     30)
                                                                                                    [(asset
                                                                                                      "SPXL"
                                                                                                      "Direxion Daily S&P 500 Bull 3x Shares")]
                                                                                                    [(weight-equal
                                                                                                      [(group
                                                                                                        "Bull or Safety Town - Base 2"
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (>
                                                                                                             (rsi
                                                                                                              "SPY"
                                                                                                              {:window
                                                                                                               126})
                                                                                                             (rsi
                                                                                                              "XLU"
                                                                                                              {:window
                                                                                                               126}))
                                                                                                            [(weight-equal
                                                                                                              [(group
                                                                                                                "Bull (Commodities?)"
                                                                                                                [(weight-equal
                                                                                                                  [(if
                                                                                                                    (<
                                                                                                                     (rsi
                                                                                                                      "XLK"
                                                                                                                      {:window
                                                                                                                       126})
                                                                                                                     (rsi
                                                                                                                      "DBC"
                                                                                                                      {:window
                                                                                                                       126}))
                                                                                                                    [(weight-equal
                                                                                                                      [(filter
                                                                                                                        (cumulative-return
                                                                                                                         {:window
                                                                                                                          5})
                                                                                                                        (select-top
                                                                                                                         1)
                                                                                                                        [(asset
                                                                                                                          "ERX"
                                                                                                                          "Direxion Daily Energy Bull 2x Shares")
                                                                                                                         (asset
                                                                                                                          "TECL"
                                                                                                                          "Direxion Daily Technology Bull 3x Shares")])])]
                                                                                                                    [(weight-equal
                                                                                                                      [(asset
                                                                                                                        "TECL"
                                                                                                                        "Direxion Daily Technology Bull 3x Shares")])])])])])]
                                                                                                            [(weight-equal
                                                                                                              [(if
                                                                                                                (<
                                                                                                                 (rsi
                                                                                                                  "TLT"
                                                                                                                  {:window
                                                                                                                   126})
                                                                                                                 50)
                                                                                                                [(weight-equal
                                                                                                                  [(group
                                                                                                                    "TECL (18.3-13.7)"
                                                                                                                    [(weight-equal
                                                                                                                      [(if
                                                                                                                        (<
                                                                                                                         (rsi
                                                                                                                          "TECL"
                                                                                                                          {:window
                                                                                                                           21})
                                                                                                                         (rsi
                                                                                                                          "AGG"
                                                                                                                          {:window
                                                                                                                           21}))
                                                                                                                        [(asset
                                                                                                                          "TECL"
                                                                                                                          "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                        [(weight-equal
                                                                                                                          [(group
                                                                                                                            "Safety Town l AR 41.9% DD 11.5% B -0.11"
                                                                                                                            [(weight-equal
                                                                                                                              [(if
                                                                                                                                (>=
                                                                                                                                 (rsi
                                                                                                                                  "SPY"
                                                                                                                                  {:window
                                                                                                                                   10})
                                                                                                                                 70)
                                                                                                                                [(weight-equal
                                                                                                                                  [(asset
                                                                                                                                    "VIXM"
                                                                                                                                    "ProShares VIX Mid-Term Futures ETF")
                                                                                                                                   (asset
                                                                                                                                    "UVXY"
                                                                                                                                    "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                                                [(weight-equal
                                                                                                                                  [(if
                                                                                                                                    (>=
                                                                                                                                     (rsi
                                                                                                                                      "SPY"
                                                                                                                                      {:window
                                                                                                                                       10})
                                                                                                                                     70)
                                                                                                                                    [(weight-equal
                                                                                                                                      [(asset
                                                                                                                                        "VIXM"
                                                                                                                                        "ProShares VIX Mid-Term Futures ETF")
                                                                                                                                       (asset
                                                                                                                                        "UVXY"
                                                                                                                                        "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                                                    [(weight-equal
                                                                                                                                      [(if
                                                                                                                                        (>
                                                                                                                                         (rsi
                                                                                                                                          "SPY"
                                                                                                                                          {:window
                                                                                                                                           126})
                                                                                                                                         (rsi
                                                                                                                                          "XLU"
                                                                                                                                          {:window
                                                                                                                                           126}))
                                                                                                                                        [(weight-equal
                                                                                                                                          [(group
                                                                                                                                            "A"
                                                                                                                                            [(weight-equal
                                                                                                                                              [(filter
                                                                                                                                                (stdev-price
                                                                                                                                                 {:window
                                                                                                                                                  21})
                                                                                                                                                (select-top
                                                                                                                                                 2)
                                                                                                                                                [(asset
                                                                                                                                                  "SVXY"
                                                                                                                                                  "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                                                 (asset
                                                                                                                                                  "VIXM"
                                                                                                                                                  "ProShares VIX Mid-Term Futures ETF")
                                                                                                                                                 (asset
                                                                                                                                                  "BTAL"
                                                                                                                                                  "AGFiQ US Market Neutral Anti-Beta Fund")])])])
                                                                                                                                           (group
                                                                                                                                            "B"
                                                                                                                                            [(weight-equal
                                                                                                                                              [(asset
                                                                                                                                                "SVXY"
                                                                                                                                                "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                                               (group
                                                                                                                                                "VIXM & BTAL"
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(asset
                                                                                                                                                    "BTAL"
                                                                                                                                                    "AGFiQ US Market Neutral Anti-Beta Fund")
                                                                                                                                                   (asset
                                                                                                                                                    "VIXM"
                                                                                                                                                    "ProShares VIX Mid-Term Futures ETF")])])])])])]
                                                                                                                                        [(weight-equal
                                                                                                                                          [(group
                                                                                                                                            "A"
                                                                                                                                            [(weight-equal
                                                                                                                                              [(filter
                                                                                                                                                (stdev-price
                                                                                                                                                 {:window
                                                                                                                                                  21})
                                                                                                                                                (select-top
                                                                                                                                                 2)
                                                                                                                                                [(asset
                                                                                                                                                  "SVXY"
                                                                                                                                                  "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                                                 (asset
                                                                                                                                                  "VIXM"
                                                                                                                                                  "ProShares VIX Mid-Term Futures ETF")
                                                                                                                                                 (asset
                                                                                                                                                  "BTAL"
                                                                                                                                                  "AGFiQ US Market Neutral Anti-Beta Fund")])])])])])])])])])])])])])])])])]
                                                                                                                [(weight-equal
                                                                                                                  [(group
                                                                                                                    "TMF or USDU"
                                                                                                                    [(weight-equal
                                                                                                                      [(filter
                                                                                                                        (rsi
                                                                                                                         {:window
                                                                                                                          21})
                                                                                                                        (select-bottom
                                                                                                                         1)
                                                                                                                        [(asset
                                                                                                                          "TMF"
                                                                                                                          "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                                                                         (asset
                                                                                                                          "USDU"
                                                                                                                          "WisdomTree Bloomberg US Dollar Bullish Fund")])])])])])])])])])])])])])])])])])])])])]
                                                                                [(weight-equal
                                                                                  [(group
                                                                                    "FTLT or Safety Town"
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (<
                                                                                         (rsi
                                                                                          "TQQQ"
                                                                                          {:window
                                                                                           10})
                                                                                         30)
                                                                                        [(asset
                                                                                          "TECL"
                                                                                          "Direxion Daily Technology Bull 3x Shares")]
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (<
                                                                                             (rsi
                                                                                              "SOXL"
                                                                                              {:window
                                                                                               10})
                                                                                             30)
                                                                                            [(asset
                                                                                              "SOXL"
                                                                                              "Direxion Daily Semiconductor Bull 3x Shares")]
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (<
                                                                                                 (rsi
                                                                                                  "SPXL"
                                                                                                  {:window
                                                                                                   10})
                                                                                                 30)
                                                                                                [(asset
                                                                                                  "SPXL"
                                                                                                  "Direxion Daily S&P 500 Bull 3x Shares")]
                                                                                                [(weight-equal
                                                                                                  [(group
                                                                                                    "Bull or Safety Town - Base 2"
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (>
                                                                                                         (rsi
                                                                                                          "SPY"
                                                                                                          {:window
                                                                                                           126})
                                                                                                         (rsi
                                                                                                          "XLU"
                                                                                                          {:window
                                                                                                           126}))
                                                                                                        [(weight-equal
                                                                                                          [(group
                                                                                                            "Bull (Commodities?)"
                                                                                                            [(weight-equal
                                                                                                              [(if
                                                                                                                (<
                                                                                                                 (rsi
                                                                                                                  "XLK"
                                                                                                                  {:window
                                                                                                                   126})
                                                                                                                 (rsi
                                                                                                                  "DBC"
                                                                                                                  {:window
                                                                                                                   126}))
                                                                                                                [(weight-equal
                                                                                                                  [(filter
                                                                                                                    (cumulative-return
                                                                                                                     {:window
                                                                                                                      5})
                                                                                                                    (select-top
                                                                                                                     1)
                                                                                                                    [(asset
                                                                                                                      "ERX"
                                                                                                                      "Direxion Daily Energy Bull 2x Shares")
                                                                                                                     (asset
                                                                                                                      "TECL"
                                                                                                                      "Direxion Daily Technology Bull 3x Shares")])])]
                                                                                                                [(weight-equal
                                                                                                                  [(asset
                                                                                                                    "TECL"
                                                                                                                    "Direxion Daily Technology Bull 3x Shares")])])])])])]
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (<
                                                                                                             (rsi
                                                                                                              "TLT"
                                                                                                              {:window
                                                                                                               126})
                                                                                                             50)
                                                                                                            [(weight-equal
                                                                                                              [(group
                                                                                                                "TECL (18.3-13.7)"
                                                                                                                [(weight-equal
                                                                                                                  [(if
                                                                                                                    (<
                                                                                                                     (rsi
                                                                                                                      "TECL"
                                                                                                                      {:window
                                                                                                                       21})
                                                                                                                     (rsi
                                                                                                                      "AGG"
                                                                                                                      {:window
                                                                                                                       21}))
                                                                                                                    [(asset
                                                                                                                      "TECL"
                                                                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                    [(weight-equal
                                                                                                                      [(group
                                                                                                                        "Safety Town l AR 41.9% DD 11.5% B -0.11"
                                                                                                                        [(weight-equal
                                                                                                                          [(if
                                                                                                                            (>=
                                                                                                                             (rsi
                                                                                                                              "SPY"
                                                                                                                              {:window
                                                                                                                               10})
                                                                                                                             70)
                                                                                                                            [(weight-equal
                                                                                                                              [(asset
                                                                                                                                "VIXM"
                                                                                                                                "ProShares VIX Mid-Term Futures ETF")
                                                                                                                               (asset
                                                                                                                                "UVXY"
                                                                                                                                "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                                            [(weight-equal
                                                                                                                              [(if
                                                                                                                                (>=
                                                                                                                                 (rsi
                                                                                                                                  "SPY"
                                                                                                                                  {:window
                                                                                                                                   10})
                                                                                                                                 70)
                                                                                                                                [(weight-equal
                                                                                                                                  [(asset
                                                                                                                                    "VIXM"
                                                                                                                                    "ProShares VIX Mid-Term Futures ETF")
                                                                                                                                   (asset
                                                                                                                                    "UVXY"
                                                                                                                                    "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                                                [(weight-equal
                                                                                                                                  [(if
                                                                                                                                    (>
                                                                                                                                     (rsi
                                                                                                                                      "SPY"
                                                                                                                                      {:window
                                                                                                                                       126})
                                                                                                                                     (rsi
                                                                                                                                      "XLU"
                                                                                                                                      {:window
                                                                                                                                       126}))
                                                                                                                                    [(weight-equal
                                                                                                                                      [(group
                                                                                                                                        "A"
                                                                                                                                        [(weight-equal
                                                                                                                                          [(filter
                                                                                                                                            (stdev-price
                                                                                                                                             {:window
                                                                                                                                              21})
                                                                                                                                            (select-top
                                                                                                                                             2)
                                                                                                                                            [(asset
                                                                                                                                              "SVXY"
                                                                                                                                              "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                                             (asset
                                                                                                                                              "VIXM"
                                                                                                                                              "ProShares VIX Mid-Term Futures ETF")
                                                                                                                                             (asset
                                                                                                                                              "BTAL"
                                                                                                                                              "AGFiQ US Market Neutral Anti-Beta Fund")])])])
                                                                                                                                       (group
                                                                                                                                        "B"
                                                                                                                                        [(weight-equal
                                                                                                                                          [(asset
                                                                                                                                            "SVXY"
                                                                                                                                            "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                                           (group
                                                                                                                                            "VIXM & BTAL"
                                                                                                                                            [(weight-equal
                                                                                                                                              [(asset
                                                                                                                                                "BTAL"
                                                                                                                                                "AGFiQ US Market Neutral Anti-Beta Fund")
                                                                                                                                               (asset
                                                                                                                                                "VIXM"
                                                                                                                                                "ProShares VIX Mid-Term Futures ETF")])])])])])]
                                                                                                                                    [(weight-equal
                                                                                                                                      [(group
                                                                                                                                        "A"
                                                                                                                                        [(weight-equal
                                                                                                                                          [(filter
                                                                                                                                            (stdev-price
                                                                                                                                             {:window
                                                                                                                                              21})
                                                                                                                                            (select-top
                                                                                                                                             2)
                                                                                                                                            [(asset
                                                                                                                                              "SVXY"
                                                                                                                                              "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                                             (asset
                                                                                                                                              "VIXM"
                                                                                                                                              "ProShares VIX Mid-Term Futures ETF")
                                                                                                                                             (asset
                                                                                                                                              "BTAL"
                                                                                                                                              "AGFiQ US Market Neutral Anti-Beta Fund")])])])])])])])])])])])])])])])])]
                                                                                                            [(weight-equal
                                                                                                              [(group
                                                                                                                "TMF or USDU"
                                                                                                                [(weight-equal
                                                                                                                  [(filter
                                                                                                                    (rsi
                                                                                                                     {:window
                                                                                                                      21})
                                                                                                                    (select-bottom
                                                                                                                     1)
                                                                                                                    [(asset
                                                                                                                      "TMF"
                                                                                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                                                                     (asset
                                                                                                                      "USDU"
                                                                                                                      "WisdomTree Bloomberg US Dollar Bullish Fund")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]
                        [(weight-equal
                          [(group
                            "Base 2 - FTLT or Bull or Bonds (UVXY)"
                            [(weight-equal
                              [(if
                                (> (rsi "QQQE" {:window 10}) 79)
                                [(asset
                                  "UVXY"
                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                [(weight-equal
                                  [(if
                                    (> (rsi "VTV" {:window 10}) 79)
                                    [(asset
                                      "UVXY"
                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                    [(weight-equal
                                      [(if
                                        (> (rsi "VOX" {:window 10}) 79)
                                        [(asset
                                          "UVXY"
                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "TECL" {:window 10})
                                             79)
                                            [(asset
                                              "UVXY"
                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "VOOG"
                                                  {:window 10})
                                                 79)
                                                [(asset
                                                  "UVXY"
                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "VOOV"
                                                      {:window 10})
                                                     79)
                                                    [(asset
                                                      "UVXY"
                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "XLP"
                                                          {:window 10})
                                                         75)
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               10})
                                                             79)
                                                            [(weight-equal
                                                              [(asset
                                                                "UVXY"
                                                                "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "XLY"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "UVXY"
                                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "FAS"
                                                                      {:window
                                                                       10})
                                                                     80)
                                                                    [(asset
                                                                      "UVXY"
                                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "SPY"
                                                                          {:window
                                                                           10})
                                                                         80)
                                                                        [(asset
                                                                          "UVXY"
                                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (<
                                                                             (cumulative-return
                                                                              "TQQQ"
                                                                              {:window
                                                                               6})
                                                                             -12)
                                                                            [(weight-equal
                                                                              [(if
                                                                                (>
                                                                                 (cumulative-return
                                                                                  "TQQQ"
                                                                                  {:window
                                                                                   1})
                                                                                 5.5)
                                                                                [(weight-equal
                                                                                  [(asset
                                                                                    "UVXY"
                                                                                    "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                [(weight-equal
                                                                                  [(group
                                                                                    "FTLT or Safety Town"
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (<
                                                                                         (rsi
                                                                                          "TQQQ"
                                                                                          {:window
                                                                                           10})
                                                                                         30)
                                                                                        [(asset
                                                                                          "TECL"
                                                                                          "Direxion Daily Technology Bull 3x Shares")]
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (<
                                                                                             (rsi
                                                                                              "SOXL"
                                                                                              {:window
                                                                                               10})
                                                                                             30)
                                                                                            [(asset
                                                                                              "SOXL"
                                                                                              "Direxion Daily Semiconductor Bull 3x Shares")]
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (<
                                                                                                 (rsi
                                                                                                  "SPXL"
                                                                                                  {:window
                                                                                                   10})
                                                                                                 30)
                                                                                                [(asset
                                                                                                  "SPXL"
                                                                                                  "Direxion Daily S&P 500 Bull 3x Shares")]
                                                                                                [(weight-equal
                                                                                                  [(group
                                                                                                    "Bull or Safety Town - Base 2"
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (>
                                                                                                         (rsi
                                                                                                          "SPY"
                                                                                                          {:window
                                                                                                           126})
                                                                                                         (rsi
                                                                                                          "XLU"
                                                                                                          {:window
                                                                                                           126}))
                                                                                                        [(weight-equal
                                                                                                          [(group
                                                                                                            "Bull (Commodities?)"
                                                                                                            [(weight-equal
                                                                                                              [(if
                                                                                                                (<
                                                                                                                 (rsi
                                                                                                                  "XLK"
                                                                                                                  {:window
                                                                                                                   126})
                                                                                                                 (rsi
                                                                                                                  "DBC"
                                                                                                                  {:window
                                                                                                                   126}))
                                                                                                                [(weight-equal
                                                                                                                  [(filter
                                                                                                                    (cumulative-return
                                                                                                                     {:window
                                                                                                                      5})
                                                                                                                    (select-top
                                                                                                                     1)
                                                                                                                    [(asset
                                                                                                                      "ERX"
                                                                                                                      "Direxion Daily Energy Bull 2x Shares")
                                                                                                                     (asset
                                                                                                                      "TECL"
                                                                                                                      "Direxion Daily Technology Bull 3x Shares")])])]
                                                                                                                [(weight-equal
                                                                                                                  [(asset
                                                                                                                    "TECL"
                                                                                                                    "Direxion Daily Technology Bull 3x Shares")])])])])])]
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (<
                                                                                                             (rsi
                                                                                                              "TLT"
                                                                                                              {:window
                                                                                                               126})
                                                                                                             50)
                                                                                                            [(weight-equal
                                                                                                              [(group
                                                                                                                "TECL (18.3-13.7)"
                                                                                                                [(weight-equal
                                                                                                                  [(if
                                                                                                                    (<
                                                                                                                     (rsi
                                                                                                                      "TECL"
                                                                                                                      {:window
                                                                                                                       21})
                                                                                                                     (rsi
                                                                                                                      "AGG"
                                                                                                                      {:window
                                                                                                                       21}))
                                                                                                                    [(asset
                                                                                                                      "TECL"
                                                                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                    [(weight-equal
                                                                                                                      [(group
                                                                                                                        "Safety Town l AR 41.9% DD 11.5% B -0.11"
                                                                                                                        [(weight-equal
                                                                                                                          [(if
                                                                                                                            (>=
                                                                                                                             (rsi
                                                                                                                              "SPY"
                                                                                                                              {:window
                                                                                                                               10})
                                                                                                                             70)
                                                                                                                            [(weight-equal
                                                                                                                              [(asset
                                                                                                                                "VIXM"
                                                                                                                                "ProShares VIX Mid-Term Futures ETF")
                                                                                                                               (asset
                                                                                                                                "UVXY"
                                                                                                                                "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                                            [(weight-equal
                                                                                                                              [(if
                                                                                                                                (>=
                                                                                                                                 (rsi
                                                                                                                                  "SPY"
                                                                                                                                  {:window
                                                                                                                                   10})
                                                                                                                                 70)
                                                                                                                                [(weight-equal
                                                                                                                                  [(asset
                                                                                                                                    "VIXM"
                                                                                                                                    "ProShares VIX Mid-Term Futures ETF")
                                                                                                                                   (asset
                                                                                                                                    "UVXY"
                                                                                                                                    "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                                                [(weight-equal
                                                                                                                                  [(if
                                                                                                                                    (>
                                                                                                                                     (rsi
                                                                                                                                      "SPY"
                                                                                                                                      {:window
                                                                                                                                       126})
                                                                                                                                     (rsi
                                                                                                                                      "XLU"
                                                                                                                                      {:window
                                                                                                                                       126}))
                                                                                                                                    [(weight-equal
                                                                                                                                      [(group
                                                                                                                                        "A"
                                                                                                                                        [(weight-equal
                                                                                                                                          [(filter
                                                                                                                                            (stdev-price
                                                                                                                                             {:window
                                                                                                                                              21})
                                                                                                                                            (select-top
                                                                                                                                             2)
                                                                                                                                            [(asset
                                                                                                                                              "SVXY"
                                                                                                                                              "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                                             (asset
                                                                                                                                              "VIXM"
                                                                                                                                              "ProShares VIX Mid-Term Futures ETF")
                                                                                                                                             (asset
                                                                                                                                              "BTAL"
                                                                                                                                              "AGFiQ US Market Neutral Anti-Beta Fund")])])])
                                                                                                                                       (group
                                                                                                                                        "B"
                                                                                                                                        [(weight-equal
                                                                                                                                          [(asset
                                                                                                                                            "SVXY"
                                                                                                                                            "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                                           (group
                                                                                                                                            "VIXM & BTAL"
                                                                                                                                            [(weight-equal
                                                                                                                                              [(asset
                                                                                                                                                "BTAL"
                                                                                                                                                "AGFiQ US Market Neutral Anti-Beta Fund")
                                                                                                                                               (asset
                                                                                                                                                "VIXM"
                                                                                                                                                "ProShares VIX Mid-Term Futures ETF")])])])])])]
                                                                                                                                    [(weight-equal
                                                                                                                                      [(group
                                                                                                                                        "A"
                                                                                                                                        [(weight-equal
                                                                                                                                          [(filter
                                                                                                                                            (stdev-price
                                                                                                                                             {:window
                                                                                                                                              21})
                                                                                                                                            (select-top
                                                                                                                                             2)
                                                                                                                                            [(asset
                                                                                                                                              "SVXY"
                                                                                                                                              "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                                             (asset
                                                                                                                                              "VIXM"
                                                                                                                                              "ProShares VIX Mid-Term Futures ETF")
                                                                                                                                             (asset
                                                                                                                                              "BTAL"
                                                                                                                                              "AGFiQ US Market Neutral Anti-Beta Fund")])])])])])])])])])])])])])])])])]
                                                                                                            [(weight-equal
                                                                                                              [(group
                                                                                                                "TMF or USDU"
                                                                                                                [(weight-equal
                                                                                                                  [(filter
                                                                                                                    (rsi
                                                                                                                     {:window
                                                                                                                      21})
                                                                                                                    (select-bottom
                                                                                                                     1)
                                                                                                                    [(asset
                                                                                                                      "TMF"
                                                                                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                                                                     (asset
                                                                                                                      "USDU"
                                                                                                                      "WisdomTree Bloomberg US Dollar Bullish Fund")])])])])])])])])])])])])])])])])])])])])]
                                                                            [(weight-equal
                                                                              [(group
                                                                                "FTLT or Safety Town"
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (<
                                                                                     (rsi
                                                                                      "TQQQ"
                                                                                      {:window
                                                                                       10})
                                                                                     30)
                                                                                    [(asset
                                                                                      "TECL"
                                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (<
                                                                                         (rsi
                                                                                          "SOXL"
                                                                                          {:window
                                                                                           10})
                                                                                         30)
                                                                                        [(asset
                                                                                          "SOXL"
                                                                                          "Direxion Daily Semiconductor Bull 3x Shares")]
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (<
                                                                                             (rsi
                                                                                              "SPXL"
                                                                                              {:window
                                                                                               10})
                                                                                             30)
                                                                                            [(asset
                                                                                              "SPXL"
                                                                                              "Direxion Daily S&P 500 Bull 3x Shares")]
                                                                                            [(weight-equal
                                                                                              [(group
                                                                                                "Bull or Safety Town - Base 2"
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (>
                                                                                                     (rsi
                                                                                                      "SPY"
                                                                                                      {:window
                                                                                                       126})
                                                                                                     (rsi
                                                                                                      "XLU"
                                                                                                      {:window
                                                                                                       126}))
                                                                                                    [(weight-equal
                                                                                                      [(group
                                                                                                        "Bull (Commodities?)"
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (<
                                                                                                             (rsi
                                                                                                              "XLK"
                                                                                                              {:window
                                                                                                               126})
                                                                                                             (rsi
                                                                                                              "DBC"
                                                                                                              {:window
                                                                                                               126}))
                                                                                                            [(weight-equal
                                                                                                              [(filter
                                                                                                                (cumulative-return
                                                                                                                 {:window
                                                                                                                  5})
                                                                                                                (select-top
                                                                                                                 1)
                                                                                                                [(asset
                                                                                                                  "ERX"
                                                                                                                  "Direxion Daily Energy Bull 2x Shares")
                                                                                                                 (asset
                                                                                                                  "TECL"
                                                                                                                  "Direxion Daily Technology Bull 3x Shares")])])]
                                                                                                            [(weight-equal
                                                                                                              [(asset
                                                                                                                "TECL"
                                                                                                                "Direxion Daily Technology Bull 3x Shares")])])])])])]
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (<
                                                                                                         (rsi
                                                                                                          "TLT"
                                                                                                          {:window
                                                                                                           126})
                                                                                                         50)
                                                                                                        [(weight-equal
                                                                                                          [(group
                                                                                                            "TECL (18.3-13.7)"
                                                                                                            [(weight-equal
                                                                                                              [(if
                                                                                                                (<
                                                                                                                 (rsi
                                                                                                                  "TECL"
                                                                                                                  {:window
                                                                                                                   21})
                                                                                                                 (rsi
                                                                                                                  "AGG"
                                                                                                                  {:window
                                                                                                                   21}))
                                                                                                                [(asset
                                                                                                                  "TECL"
                                                                                                                  "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                [(weight-equal
                                                                                                                  [(group
                                                                                                                    "Safety Town l AR 41.9% DD 11.5% B -0.11"
                                                                                                                    [(weight-equal
                                                                                                                      [(if
                                                                                                                        (>=
                                                                                                                         (rsi
                                                                                                                          "SPY"
                                                                                                                          {:window
                                                                                                                           10})
                                                                                                                         70)
                                                                                                                        [(weight-equal
                                                                                                                          [(asset
                                                                                                                            "VIXM"
                                                                                                                            "ProShares VIX Mid-Term Futures ETF")
                                                                                                                           (asset
                                                                                                                            "UVXY"
                                                                                                                            "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                                        [(weight-equal
                                                                                                                          [(if
                                                                                                                            (>=
                                                                                                                             (rsi
                                                                                                                              "SPY"
                                                                                                                              {:window
                                                                                                                               10})
                                                                                                                             70)
                                                                                                                            [(weight-equal
                                                                                                                              [(asset
                                                                                                                                "VIXM"
                                                                                                                                "ProShares VIX Mid-Term Futures ETF")
                                                                                                                               (asset
                                                                                                                                "UVXY"
                                                                                                                                "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                                            [(weight-equal
                                                                                                                              [(if
                                                                                                                                (>
                                                                                                                                 (rsi
                                                                                                                                  "SPY"
                                                                                                                                  {:window
                                                                                                                                   126})
                                                                                                                                 (rsi
                                                                                                                                  "XLU"
                                                                                                                                  {:window
                                                                                                                                   126}))
                                                                                                                                [(weight-equal
                                                                                                                                  [(group
                                                                                                                                    "A"
                                                                                                                                    [(weight-equal
                                                                                                                                      [(filter
                                                                                                                                        (stdev-price
                                                                                                                                         {:window
                                                                                                                                          21})
                                                                                                                                        (select-top
                                                                                                                                         2)
                                                                                                                                        [(asset
                                                                                                                                          "SVXY"
                                                                                                                                          "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                                         (asset
                                                                                                                                          "VIXM"
                                                                                                                                          "ProShares VIX Mid-Term Futures ETF")
                                                                                                                                         (asset
                                                                                                                                          "BTAL"
                                                                                                                                          "AGFiQ US Market Neutral Anti-Beta Fund")])])])
                                                                                                                                   (group
                                                                                                                                    "B"
                                                                                                                                    [(weight-equal
                                                                                                                                      [(asset
                                                                                                                                        "SVXY"
                                                                                                                                        "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                                       (group
                                                                                                                                        "VIXM & BTAL"
                                                                                                                                        [(weight-equal
                                                                                                                                          [(asset
                                                                                                                                            "BTAL"
                                                                                                                                            "AGFiQ US Market Neutral Anti-Beta Fund")
                                                                                                                                           (asset
                                                                                                                                            "VIXM"
                                                                                                                                            "ProShares VIX Mid-Term Futures ETF")])])])])])]
                                                                                                                                [(weight-equal
                                                                                                                                  [(group
                                                                                                                                    "A"
                                                                                                                                    [(weight-equal
                                                                                                                                      [(filter
                                                                                                                                        (stdev-price
                                                                                                                                         {:window
                                                                                                                                          21})
                                                                                                                                        (select-top
                                                                                                                                         2)
                                                                                                                                        [(asset
                                                                                                                                          "SVXY"
                                                                                                                                          "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                                         (asset
                                                                                                                                          "VIXM"
                                                                                                                                          "ProShares VIX Mid-Term Futures ETF")
                                                                                                                                         (asset
                                                                                                                                          "BTAL"
                                                                                                                                          "AGFiQ US Market Neutral Anti-Beta Fund")])])])])])])])])])])])])])])])])]
                                                                                                        [(weight-equal
                                                                                                          [(group
                                                                                                            "TMF or USDU"
                                                                                                            [(weight-equal
                                                                                                              [(filter
                                                                                                                (rsi
                                                                                                                 {:window
                                                                                                                  21})
                                                                                                                (select-bottom
                                                                                                                 1)
                                                                                                                [(asset
                                                                                                                  "TMF"
                                                                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                                                                 (asset
                                                                                                                  "USDU"
                                                                                                                  "WisdomTree Bloomberg US Dollar Bullish Fund")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]
        [(weight-equal
          [(group
            "Base 2 - FTLT or Bull or Bonds (UVXY)"
            [(weight-equal
              [(if
                (> (rsi "QQQE" {:window 10}) 79)
                [(asset
                  "UVXY"
                  "ProShares Ultra VIX Short-Term Futures ETF")]
                [(weight-equal
                  [(if
                    (> (rsi "VTV" {:window 10}) 79)
                    [(asset
                      "UVXY"
                      "ProShares Ultra VIX Short-Term Futures ETF")]
                    [(weight-equal
                      [(if
                        (> (rsi "VOX" {:window 10}) 79)
                        [(asset
                          "UVXY"
                          "ProShares Ultra VIX Short-Term Futures ETF")]
                        [(weight-equal
                          [(if
                            (> (rsi "TECL" {:window 10}) 79)
                            [(asset
                              "UVXY"
                              "ProShares Ultra VIX Short-Term Futures ETF")]
                            [(weight-equal
                              [(if
                                (> (rsi "VOOG" {:window 10}) 79)
                                [(asset
                                  "UVXY"
                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                [(weight-equal
                                  [(if
                                    (> (rsi "VOOV" {:window 10}) 79)
                                    [(asset
                                      "UVXY"
                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                    [(weight-equal
                                      [(if
                                        (> (rsi "XLP" {:window 10}) 75)
                                        [(asset
                                          "UVXY"
                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "TQQQ" {:window 10})
                                             79)
                                            [(weight-equal
                                              [(asset
                                                "UVXY"
                                                "ProShares Ultra VIX Short-Term Futures ETF")])]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "XLY"
                                                  {:window 10})
                                                 80)
                                                [(asset
                                                  "UVXY"
                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "FAS"
                                                      {:window 10})
                                                     80)
                                                    [(asset
                                                      "UVXY"
                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "SPY"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "TQQQ"
                                                              {:window
                                                               6})
                                                             -12)
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (cumulative-return
                                                                  "TQQQ"
                                                                  {:window
                                                                   1})
                                                                 5.5)
                                                                [(weight-equal
                                                                  [(asset
                                                                    "UVXY"
                                                                    "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                [(weight-equal
                                                                  [(group
                                                                    "FTLT or Safety Town"
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "TQQQ"
                                                                          {:window
                                                                           10})
                                                                         30)
                                                                        [(asset
                                                                          "TECL"
                                                                          "Direxion Daily Technology Bull 3x Shares")]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (<
                                                                             (rsi
                                                                              "SOXL"
                                                                              {:window
                                                                               10})
                                                                             30)
                                                                            [(asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")]
                                                                            [(weight-equal
                                                                              [(if
                                                                                (<
                                                                                 (rsi
                                                                                  "SPXL"
                                                                                  {:window
                                                                                   10})
                                                                                 30)
                                                                                [(asset
                                                                                  "SPXL"
                                                                                  "Direxion Daily S&P 500 Bull 3x Shares")]
                                                                                [(weight-equal
                                                                                  [(group
                                                                                    "Bull or Safety Town - Base 2"
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (rsi
                                                                                          "SPY"
                                                                                          {:window
                                                                                           126})
                                                                                         (rsi
                                                                                          "XLU"
                                                                                          {:window
                                                                                           126}))
                                                                                        [(weight-equal
                                                                                          [(group
                                                                                            "Bull (Commodities?)"
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (<
                                                                                                 (rsi
                                                                                                  "XLK"
                                                                                                  {:window
                                                                                                   126})
                                                                                                 (rsi
                                                                                                  "DBC"
                                                                                                  {:window
                                                                                                   126}))
                                                                                                [(weight-equal
                                                                                                  [(filter
                                                                                                    (cumulative-return
                                                                                                     {:window
                                                                                                      5})
                                                                                                    (select-top
                                                                                                     1)
                                                                                                    [(asset
                                                                                                      "ERX"
                                                                                                      "Direxion Daily Energy Bull 2x Shares")
                                                                                                     (asset
                                                                                                      "TECL"
                                                                                                      "Direxion Daily Technology Bull 3x Shares")])])]
                                                                                                [(weight-equal
                                                                                                  [(asset
                                                                                                    "TECL"
                                                                                                    "Direxion Daily Technology Bull 3x Shares")])])])])])]
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (<
                                                                                             (rsi
                                                                                              "TLT"
                                                                                              {:window
                                                                                               126})
                                                                                             50)
                                                                                            [(weight-equal
                                                                                              [(group
                                                                                                "TECL (18.3-13.7)"
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (<
                                                                                                     (rsi
                                                                                                      "TECL"
                                                                                                      {:window
                                                                                                       21})
                                                                                                     (rsi
                                                                                                      "AGG"
                                                                                                      {:window
                                                                                                       21}))
                                                                                                    [(asset
                                                                                                      "TECL"
                                                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                                                    [(weight-equal
                                                                                                      [(group
                                                                                                        "Safety Town l AR 41.9% DD 11.5% B -0.11"
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (>=
                                                                                                             (rsi
                                                                                                              "SPY"
                                                                                                              {:window
                                                                                                               10})
                                                                                                             70)
                                                                                                            [(weight-equal
                                                                                                              [(asset
                                                                                                                "VIXM"
                                                                                                                "ProShares VIX Mid-Term Futures ETF")
                                                                                                               (asset
                                                                                                                "UVXY"
                                                                                                                "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                            [(weight-equal
                                                                                                              [(if
                                                                                                                (>=
                                                                                                                 (rsi
                                                                                                                  "SPY"
                                                                                                                  {:window
                                                                                                                   10})
                                                                                                                 70)
                                                                                                                [(weight-equal
                                                                                                                  [(asset
                                                                                                                    "VIXM"
                                                                                                                    "ProShares VIX Mid-Term Futures ETF")
                                                                                                                   (asset
                                                                                                                    "UVXY"
                                                                                                                    "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                                [(weight-equal
                                                                                                                  [(if
                                                                                                                    (>
                                                                                                                     (rsi
                                                                                                                      "SPY"
                                                                                                                      {:window
                                                                                                                       126})
                                                                                                                     (rsi
                                                                                                                      "XLU"
                                                                                                                      {:window
                                                                                                                       126}))
                                                                                                                    [(weight-equal
                                                                                                                      [(group
                                                                                                                        "A"
                                                                                                                        [(weight-equal
                                                                                                                          [(filter
                                                                                                                            (stdev-price
                                                                                                                             {:window
                                                                                                                              21})
                                                                                                                            (select-top
                                                                                                                             2)
                                                                                                                            [(asset
                                                                                                                              "SVXY"
                                                                                                                              "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                             (asset
                                                                                                                              "VIXM"
                                                                                                                              "ProShares VIX Mid-Term Futures ETF")
                                                                                                                             (asset
                                                                                                                              "BTAL"
                                                                                                                              "AGFiQ US Market Neutral Anti-Beta Fund")])])])
                                                                                                                       (group
                                                                                                                        "B"
                                                                                                                        [(weight-equal
                                                                                                                          [(asset
                                                                                                                            "SVXY"
                                                                                                                            "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                           (group
                                                                                                                            "VIXM & BTAL"
                                                                                                                            [(weight-equal
                                                                                                                              [(asset
                                                                                                                                "BTAL"
                                                                                                                                "AGFiQ US Market Neutral Anti-Beta Fund")
                                                                                                                               (asset
                                                                                                                                "VIXM"
                                                                                                                                "ProShares VIX Mid-Term Futures ETF")])])])])])]
                                                                                                                    [(weight-equal
                                                                                                                      [(group
                                                                                                                        "A"
                                                                                                                        [(weight-equal
                                                                                                                          [(filter
                                                                                                                            (stdev-price
                                                                                                                             {:window
                                                                                                                              21})
                                                                                                                            (select-top
                                                                                                                             2)
                                                                                                                            [(asset
                                                                                                                              "SVXY"
                                                                                                                              "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                             (asset
                                                                                                                              "VIXM"
                                                                                                                              "ProShares VIX Mid-Term Futures ETF")
                                                                                                                             (asset
                                                                                                                              "BTAL"
                                                                                                                              "AGFiQ US Market Neutral Anti-Beta Fund")])])])])])])])])])])])])])])])])]
                                                                                            [(weight-equal
                                                                                              [(group
                                                                                                "TMF or USDU"
                                                                                                [(weight-equal
                                                                                                  [(filter
                                                                                                    (rsi
                                                                                                     {:window
                                                                                                      21})
                                                                                                    (select-bottom
                                                                                                     1)
                                                                                                    [(asset
                                                                                                      "TMF"
                                                                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                                                     (asset
                                                                                                      "USDU"
                                                                                                      "WisdomTree Bloomberg US Dollar Bullish Fund")])])])])])])])])])])])])])])])])])])])])]
                                                            [(weight-equal
                                                              [(group
                                                                "FTLT or Safety Town"
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (rsi
                                                                      "TQQQ"
                                                                      {:window
                                                                       10})
                                                                     30)
                                                                    [(asset
                                                                      "TECL"
                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "SOXL"
                                                                          {:window
                                                                           10})
                                                                         30)
                                                                        [(asset
                                                                          "SOXL"
                                                                          "Direxion Daily Semiconductor Bull 3x Shares")]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (<
                                                                             (rsi
                                                                              "SPXL"
                                                                              {:window
                                                                               10})
                                                                             30)
                                                                            [(asset
                                                                              "SPXL"
                                                                              "Direxion Daily S&P 500 Bull 3x Shares")]
                                                                            [(weight-equal
                                                                              [(group
                                                                                "Bull or Safety Town - Base 2"
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (>
                                                                                     (rsi
                                                                                      "SPY"
                                                                                      {:window
                                                                                       126})
                                                                                     (rsi
                                                                                      "XLU"
                                                                                      {:window
                                                                                       126}))
                                                                                    [(weight-equal
                                                                                      [(group
                                                                                        "Bull (Commodities?)"
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (<
                                                                                             (rsi
                                                                                              "XLK"
                                                                                              {:window
                                                                                               126})
                                                                                             (rsi
                                                                                              "DBC"
                                                                                              {:window
                                                                                               126}))
                                                                                            [(weight-equal
                                                                                              [(filter
                                                                                                (cumulative-return
                                                                                                 {:window
                                                                                                  5})
                                                                                                (select-top
                                                                                                 1)
                                                                                                [(asset
                                                                                                  "ERX"
                                                                                                  "Direxion Daily Energy Bull 2x Shares")
                                                                                                 (asset
                                                                                                  "TECL"
                                                                                                  "Direxion Daily Technology Bull 3x Shares")])])]
                                                                                            [(weight-equal
                                                                                              [(asset
                                                                                                "TECL"
                                                                                                "Direxion Daily Technology Bull 3x Shares")])])])])])]
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (<
                                                                                         (rsi
                                                                                          "TLT"
                                                                                          {:window
                                                                                           126})
                                                                                         50)
                                                                                        [(weight-equal
                                                                                          [(group
                                                                                            "TECL (18.3-13.7)"
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (<
                                                                                                 (rsi
                                                                                                  "TECL"
                                                                                                  {:window
                                                                                                   21})
                                                                                                 (rsi
                                                                                                  "AGG"
                                                                                                  {:window
                                                                                                   21}))
                                                                                                [(asset
                                                                                                  "TECL"
                                                                                                  "Direxion Daily Technology Bull 3x Shares")]
                                                                                                [(weight-equal
                                                                                                  [(group
                                                                                                    "Safety Town l AR 41.9% DD 11.5% B -0.11"
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (>=
                                                                                                         (rsi
                                                                                                          "SPY"
                                                                                                          {:window
                                                                                                           10})
                                                                                                         70)
                                                                                                        [(weight-equal
                                                                                                          [(asset
                                                                                                            "VIXM"
                                                                                                            "ProShares VIX Mid-Term Futures ETF")
                                                                                                           (asset
                                                                                                            "UVXY"
                                                                                                            "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (>=
                                                                                                             (rsi
                                                                                                              "SPY"
                                                                                                              {:window
                                                                                                               10})
                                                                                                             70)
                                                                                                            [(weight-equal
                                                                                                              [(asset
                                                                                                                "VIXM"
                                                                                                                "ProShares VIX Mid-Term Futures ETF")
                                                                                                               (asset
                                                                                                                "UVXY"
                                                                                                                "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                            [(weight-equal
                                                                                                              [(if
                                                                                                                (>
                                                                                                                 (rsi
                                                                                                                  "SPY"
                                                                                                                  {:window
                                                                                                                   126})
                                                                                                                 (rsi
                                                                                                                  "XLU"
                                                                                                                  {:window
                                                                                                                   126}))
                                                                                                                [(weight-equal
                                                                                                                  [(group
                                                                                                                    "A"
                                                                                                                    [(weight-equal
                                                                                                                      [(filter
                                                                                                                        (stdev-price
                                                                                                                         {:window
                                                                                                                          21})
                                                                                                                        (select-top
                                                                                                                         2)
                                                                                                                        [(asset
                                                                                                                          "SVXY"
                                                                                                                          "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                         (asset
                                                                                                                          "VIXM"
                                                                                                                          "ProShares VIX Mid-Term Futures ETF")
                                                                                                                         (asset
                                                                                                                          "BTAL"
                                                                                                                          "AGFiQ US Market Neutral Anti-Beta Fund")])])])
                                                                                                                   (group
                                                                                                                    "B"
                                                                                                                    [(weight-equal
                                                                                                                      [(asset
                                                                                                                        "SVXY"
                                                                                                                        "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                       (group
                                                                                                                        "VIXM & BTAL"
                                                                                                                        [(weight-equal
                                                                                                                          [(asset
                                                                                                                            "BTAL"
                                                                                                                            "AGFiQ US Market Neutral Anti-Beta Fund")
                                                                                                                           (asset
                                                                                                                            "VIXM"
                                                                                                                            "ProShares VIX Mid-Term Futures ETF")])])])])])]
                                                                                                                [(weight-equal
                                                                                                                  [(group
                                                                                                                    "A"
                                                                                                                    [(weight-equal
                                                                                                                      [(filter
                                                                                                                        (stdev-price
                                                                                                                         {:window
                                                                                                                          21})
                                                                                                                        (select-top
                                                                                                                         2)
                                                                                                                        [(asset
                                                                                                                          "SVXY"
                                                                                                                          "ProShares Short VIX Short-Term Futures ETF")
                                                                                                                         (asset
                                                                                                                          "VIXM"
                                                                                                                          "ProShares VIX Mid-Term Futures ETF")
                                                                                                                         (asset
                                                                                                                          "BTAL"
                                                                                                                          "AGFiQ US Market Neutral Anti-Beta Fund")])])])])])])])])])])])])])])])])]
                                                                                        [(weight-equal
                                                                                          [(group
                                                                                            "TMF or USDU"
                                                                                            [(weight-equal
                                                                                              [(filter
                                                                                                (rsi
                                                                                                 {:window
                                                                                                  21})
                                                                                                (select-bottom
                                                                                                 1)
                                                                                                [(asset
                                                                                                  "TMF"
                                                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                                                 (asset
                                                                                                  "USDU"
                                                                                                  "WisdomTree Bloomberg US Dollar Bullish Fund")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]))
