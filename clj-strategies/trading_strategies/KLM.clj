(defsymphony
 "KMLM sorter V4 - Added back nerfed Nova version"
 {:asset-class "EQUITIES", :rebalance-threshold 0.1}
 (weight-equal
  [(filter
    (stdev-return {:window 5})
    (select-top 1)
    [(group
      "506/38 KMLM (13) - Longer BT"
      [(weight-equal
        [(group
          "KMLM switcher (single pops)| BT 4/13/22 = A.R. 466% / D.D. 22%"
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
                                               (rsi "XLY" {:window 10})
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
                                                        [(group
                                                          "Single Popped KMLM"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (rsi
                                                                "UVXY"
                                                                {:window
                                                                 21})
                                                               65)
                                                              [(weight-equal
                                                                [(group
                                                                  "BSC"
                                                                  [(weight-equal
                                                                    [(if
                                                                      (>
                                                                       (rsi
                                                                        "SPY"
                                                                        {:window
                                                                         21})
                                                                       30)
                                                                      [(asset
                                                                        "VIXM"
                                                                        "ProShares VIX Mid-Term Futures ETF")]
                                                                      [(asset
                                                                        "SPXL"
                                                                        "Direxion Daily S&P 500 Bull 3x Shares")])])])])]
                                                              [(weight-equal
                                                                [(group
                                                                  "Combined Pop Bot"
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
                                                                                  "Copypasta YOLO GainZs Here"
                                                                                  [(weight-equal
                                                                                    [(group
                                                                                      "KMLM switcher: TECL, SVIX, or L/S Rotator | BT 4/13/22 = AR 164% / DD 22.2%"
                                                                                      [(weight-equal
                                                                                        [(if
                                                                                          (>
                                                                                           (rsi
                                                                                            "XLK"
                                                                                            {:window
                                                                                             10})
                                                                                           (rsi
                                                                                            "KMLM"
                                                                                            {:window
                                                                                             10}))
                                                                                          [(weight-equal
                                                                                            [(filter
                                                                                              (rsi
                                                                                               {:window
                                                                                                10})
                                                                                              (select-bottom
                                                                                               1)
                                                                                              [(asset
                                                                                                "FNGU"
                                                                                                "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                                                          [(group
                                                                                            "Long/Short Rotator with FTLS KMLM SSO UUP | BT 12/10/20 | 15.1/3.5  "
                                                                                            [(weight-equal
                                                                                              [(filter
                                                                                                (stdev-return
                                                                                                 {:window
                                                                                                  6})
                                                                                                (select-bottom
                                                                                                 1)
                                                                                                [(asset
                                                                                                  "UUP"
                                                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                                                 (asset
                                                                                                  "FTLS"
                                                                                                  "First Trust Long/Short Equity ETF")
                                                                                                 (asset
                                                                                                  "KMLM"
                                                                                                  "KFA Mount Lucas Managed Futures Index Strategy ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
     (group
      "1280/26 KMLM (50)"
      [(weight-equal
        [(group
          "KMLM switcher (single pops)| BT 4/13/22 = A.R. 466% / D.D. 22%"
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
                                               (rsi "XLY" {:window 10})
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
                                                      [(group
                                                        "Combined Pop Bot"
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
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "LABU"
                                                                          {:window
                                                                           10})
                                                                         25)
                                                                        [(asset
                                                                          "LABU"
                                                                          "Direxion Daily S&P Biotech Bull 3X Shares")]
                                                                        [(group
                                                                          "KMLM switcher: TECL, SVIX, or L/S Rotator | BT 4/13/22 = AR 164% / DD 22.2%"
                                                                          [(weight-equal
                                                                            [(if
                                                                              (>
                                                                               (rsi
                                                                                "XLK"
                                                                                {:window
                                                                                 10})
                                                                               (rsi
                                                                                "KMLM"
                                                                                {:window
                                                                                 10}))
                                                                              [(weight-equal
                                                                                [(filter
                                                                                  (rsi
                                                                                   {:window
                                                                                    10})
                                                                                  (select-bottom
                                                                                   2)
                                                                                  [(asset
                                                                                    "TECL"
                                                                                    "Direxion Daily Technology Bull 3x Shares")
                                                                                   (asset
                                                                                    "SOXL"
                                                                                    "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                   (asset
                                                                                    "SVIX"
                                                                                    "-1x Short VIX Futures ETF")])])]
                                                                              [(weight-equal
                                                                                [(filter
                                                                                  (rsi
                                                                                   {:window
                                                                                    10})
                                                                                  (select-top
                                                                                   1)
                                                                                  [(asset
                                                                                    "SQQQ"
                                                                                    "ProShares UltraPro Short QQQ")
                                                                                   (asset
                                                                                    "TLT"
                                                                                    "iShares 20+ Year Treasury Bond ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
     (group
      "1200/28 KMLM (43)"
      [(weight-equal
        [(group
          "KMLM switcher (single pops)| BT 4/13/22 = A.R. 466% / D.D. 22%"
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
                                               (rsi "XLY" {:window 10})
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
                                                        [(group
                                                          "Single Popped KMLM"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (rsi
                                                                "UVXY"
                                                                {:window
                                                                 21})
                                                               65)
                                                              [(weight-equal
                                                                [(group
                                                                  "BSC"
                                                                  [(weight-equal
                                                                    [(if
                                                                      (>
                                                                       (rsi
                                                                        "SPY"
                                                                        {:window
                                                                         21})
                                                                       30)
                                                                      [(asset
                                                                        "VIXM"
                                                                        "ProShares VIX Mid-Term Futures ETF")]
                                                                      [(asset
                                                                        "SPXL"
                                                                        "Direxion Daily S&P 500 Bull 3x Shares")])])])])]
                                                              [(weight-equal
                                                                [(group
                                                                  "Combined Pop Bot"
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
                                                                                  "Copypasta YOLO GainZs Here"
                                                                                  [(weight-equal
                                                                                    [(group
                                                                                      "KMLM switcher: TECL, SVIX, or L/S Rotator | BT 4/13/22 = AR 164% / DD 22.2%"
                                                                                      [(weight-equal
                                                                                        [(if
                                                                                          (>
                                                                                           (rsi
                                                                                            "XLK"
                                                                                            {:window
                                                                                             10})
                                                                                           (rsi
                                                                                            "KMLM"
                                                                                            {:window
                                                                                             10}))
                                                                                          [(weight-equal
                                                                                            [(filter
                                                                                              (rsi
                                                                                               {:window
                                                                                                10})
                                                                                              (select-bottom
                                                                                               1)
                                                                                              [(asset
                                                                                                "TECL"
                                                                                                "Direxion Daily Technology Bull 3x Shares")
                                                                                               (asset
                                                                                                "SOXL"
                                                                                                "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                               (asset
                                                                                                "SVIX"
                                                                                                "-1x Short VIX Futures ETF")])])]
                                                                                          [(weight-equal
                                                                                            [(filter
                                                                                              (rsi
                                                                                               {:window
                                                                                                10})
                                                                                              (select-top
                                                                                               1)
                                                                                              [(asset
                                                                                                "SQQQ"
                                                                                                "ProShares UltraPro Short QQQ")
                                                                                               (asset
                                                                                                "TLT"
                                                                                                "iShares 20+ Year Treasury Bond ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
     (group
      "520/22 KMLM (23) - Original"
      [(weight-equal
        [(group
          "KMLM switcher (single pops)| BT 4/13/22 = A.R. 466% / D.D. 22%"
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
                                               (rsi "XLY" {:window 10})
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
                                                        [(group
                                                          "Single Popped KMLM"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (rsi
                                                                "UVXY"
                                                                {:window
                                                                 21})
                                                               65)
                                                              [(weight-equal
                                                                [(group
                                                                  "BSC"
                                                                  [(weight-equal
                                                                    [(if
                                                                      (>
                                                                       (rsi
                                                                        "SPY"
                                                                        {:window
                                                                         21})
                                                                       30)
                                                                      [(asset
                                                                        "VIXM"
                                                                        "ProShares VIX Mid-Term Futures ETF")]
                                                                      [(asset
                                                                        "SPXL"
                                                                        "Direxion Daily S&P 500 Bull 3x Shares")])])])])]
                                                              [(weight-equal
                                                                [(group
                                                                  "Combined Pop Bot"
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
                                                                                  "Copypasta YOLO GainZs Here"
                                                                                  [(weight-equal
                                                                                    [(group
                                                                                      "KMLM switcher: TECL, SVIX, or L/S Rotator | BT 4/13/22 = AR 164% / DD 22.2%"
                                                                                      [(weight-equal
                                                                                        [(if
                                                                                          (>
                                                                                           (rsi
                                                                                            "XLK"
                                                                                            {:window
                                                                                             10})
                                                                                           (rsi
                                                                                            "KMLM"
                                                                                            {:window
                                                                                             10}))
                                                                                          [(weight-equal
                                                                                            [(filter
                                                                                              (rsi
                                                                                               {:window
                                                                                                10})
                                                                                              (select-bottom
                                                                                               1)
                                                                                              [(asset
                                                                                                "TECL"
                                                                                                "Direxion Daily Technology Bull 3x Shares")
                                                                                               (asset
                                                                                                "SVIX"
                                                                                                "-1x Short VIX Futures ETF")])])]
                                                                                          [(group
                                                                                            "Long/Short Rotator with FTLS KMLM SSO UUP | BT 12/10/20 | 15.1/3.5  "
                                                                                            [(weight-equal
                                                                                              [(filter
                                                                                                (stdev-return
                                                                                                 {:window
                                                                                                  6})
                                                                                                (select-bottom
                                                                                                 3)
                                                                                                [(asset
                                                                                                  "TMV"
                                                                                                  nil)
                                                                                                 (asset
                                                                                                  "TMF"
                                                                                                  nil)
                                                                                                 (asset
                                                                                                  "SVXY"
                                                                                                  nil)
                                                                                                 (asset
                                                                                                  "VIXM"
                                                                                                  nil)
                                                                                                 (asset
                                                                                                  "FTLS"
                                                                                                  "First Trust Long/Short Equity ETF")
                                                                                                 (asset
                                                                                                  "KMLM"
                                                                                                  "KFA Mount Lucas Managed Futures Index Strategy ETF")
                                                                                                 (asset
                                                                                                  "UUP"
                                                                                                  "Invesco DB US Dollar Index Bullish Fund")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
     (group
      "530/18 (29)"
      [(weight-equal
        [(group
          "KMLM Switcher | Anansi Mods"
          [(weight-equal
            [(if
              (> (rsi "SPY" {:window 10}) 80)
              [(group
                "Scale-In | VIX+ -> VIX++"
                [(weight-equal
                  [(if
                    (> (rsi "SPY" {:window 10}) 82.5)
                    [(group
                      "VIX Blend++"
                      [(weight-equal
                        [(asset "UVXY" nil)
                         (asset "UVXY" nil)
                         (asset "VIXM" nil)])])]
                    [(group
                      "VIX Blend+"
                      [(weight-equal
                        [(asset "UVXY" nil)
                         (asset "VXX" nil)
                         (asset "VIXM" nil)])])])])])]
              [(weight-equal
                [(if
                  (> (rsi "IOO" {:window 10}) 80)
                  [(group
                    "Scale-In | VIX+ -> VIX++"
                    [(weight-equal
                      [(if
                        (> (rsi "IOO" {:window 10}) 82.5)
                        [(group
                          "VIX Blend++"
                          [(weight-equal
                            [(asset "UVXY" nil)
                             (asset "UVXY" nil)
                             (asset "VIXM" nil)])])]
                        [(group
                          "VIX Blend+"
                          [(weight-equal
                            [(asset "UVXY" nil)
                             (asset "VXX" nil)
                             (asset "VIXM" nil)])])])])])]
                  [(weight-equal
                    [(if
                      (> (rsi "QQQ" {:window 10}) 79)
                      [(group
                        "Scale-In | VIX+ -> VIX++"
                        [(weight-equal
                          [(if
                            (> (rsi "QQQ" {:window 10}) 82.5)
                            [(group
                              "VIX Blend++"
                              [(weight-equal
                                [(asset "UVXY" nil)
                                 (asset "UVXY" nil)
                                 (asset "VIXM" nil)])])]
                            [(group
                              "VIX Blend+"
                              [(weight-equal
                                [(asset "UVXY" nil)
                                 (asset "VXX" nil)
                                 (asset "VIXM" nil)])])])])])]
                      [(weight-equal
                        [(if
                          (> (rsi "VTV" {:window 10}) 79)
                          [(group
                            "Scale-In | VIX -> VIX+"
                            [(weight-equal
                              [(if
                                (> (rsi "VTV" {:window 10}) 85)
                                [(group
                                  "VIX Blend+"
                                  [(weight-equal
                                    [(asset "UVXY" nil)
                                     (asset "VXX" nil)
                                     (asset "VIXM" nil)])])]
                                [(group
                                  "VIX Blend"
                                  [(weight-equal
                                    [(asset "VIXY" nil)
                                     (asset "VXX" nil)
                                     (asset "VIXM" nil)])])])])])]
                          [(weight-equal
                            [(if
                              (> (rsi "XLP" {:window 10}) 77)
                              [(group
                                "Scale-In | VIX -> VIX+"
                                [(weight-equal
                                  [(if
                                    (> (rsi "XLP" {:window 10}) 85)
                                    [(group
                                      "VIX Blend+"
                                      [(weight-equal
                                        [(asset "UVXY" nil)
                                         (asset "VXX" nil)
                                         (asset "VIXM" nil)])])]
                                    [(group
                                      "VIX Blend"
                                      [(weight-equal
                                        [(asset "VIXY" nil)
                                         (asset "VXX" nil)
                                         (asset "VIXM" nil)])])])])])]
                              [(weight-equal
                                [(if
                                  (> (rsi "XLF" {:window 10}) 81)
                                  [(group
                                    "Scale-In | VIX -> VIX+"
                                    [(weight-equal
                                      [(if
                                        (> (rsi "XLF" {:window 10}) 85)
                                        [(group
                                          "VIX Blend+"
                                          [(weight-equal
                                            [(asset "UVXY" nil)
                                             (asset "VXX" nil)
                                             (asset "VIXM" nil)])])]
                                        [(group
                                          "VIX Blend"
                                          [(weight-equal
                                            [(asset "VIXY" nil)
                                             (asset "VXX" nil)
                                             (asset
                                              "VIXM"
                                              nil)])])])])])]
                                  [(weight-equal
                                    [(if
                                      (> (rsi "RETL" {:window 10}) 82)
                                      [(group
                                        "Scale-In | BTAL -> VIX"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "RETL" {:window 10})
                                             85)
                                            [(group
                                              "VIX Blend"
                                              [(weight-equal
                                                [(asset "VIXY" nil)
                                                 (asset "VXX" nil)
                                                 (asset
                                                  "VIXM"
                                                  nil)])])]
                                            [(group
                                              "BTAL/BIL"
                                              [(weight-equal
                                                [(asset "BTAL" nil)
                                                 (asset
                                                  "BIL"
                                                  nil)])])])])])]
                                      [(weight-equal
                                        [(if
                                          (>
                                           (rsi "SPY" {:window 70})
                                           63)
                                          [(group
                                            "Overbought"
                                            [(weight-equal
                                              [(group
                                                "AGG > QQQ"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "AGG"
                                                      {:window 15})
                                                     (rsi
                                                      "QQQ"
                                                      {:window 15}))
                                                    [(group
                                                      "All 3x Tech"
                                                      [(weight-equal
                                                        [(asset
                                                          "TQQQ"
                                                          nil)
                                                         (asset
                                                          "SPXL"
                                                          nil)
                                                         (asset
                                                          "SOXL"
                                                          nil)
                                                         (asset
                                                          "FNGU"
                                                          nil)
                                                         (asset
                                                          "ERX"
                                                          nil)])])]
                                                    [(group
                                                      "GLD/SLV/PDBC"
                                                      [(weight-specified
                                                        0.5
                                                        (asset
                                                         "GLD"
                                                         nil)
                                                        0.25
                                                        (asset
                                                         "SLV"
                                                         nil)
                                                        0.25
                                                        (asset
                                                         "PDBC"
                                                         nil))])])])])
                                               (group
                                                "VIX or Commodities"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "QQQ"
                                                      {:window 90})
                                                     60)
                                                    [(asset
                                                      "VIXY"
                                                      nil)]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "QQQ"
                                                          {:window 14})
                                                         80)
                                                        [(asset
                                                          "VIXY"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "QQQ"
                                                              {:window
                                                               5})
                                                             90)
                                                            [(asset
                                                              "VIXY"
                                                              nil)]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "QQQ"
                                                                  {:window
                                                                   3})
                                                                 95)
                                                                [(asset
                                                                  "VIXY"
                                                                  nil)]
                                                                [(group
                                                                  "GLD/SLV/PDBC"
                                                                  [(weight-specified
                                                                    0.5
                                                                    (asset
                                                                     "GLD"
                                                                     nil)
                                                                    0.25
                                                                    (asset
                                                                     "SLV"
                                                                     nil)
                                                                    0.25
                                                                    (asset
                                                                     "PDBC"
                                                                     nil))])])])])])])])])])])])])]
                                          [(group
                                            "10. KMLM Switcher | Holy Grail"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "VOX"
                                                  {:window 10})
                                                 79)
                                                [(group
                                                  "VIX Blend"
                                                  [(weight-equal
                                                    [(asset "VIXY" nil)
                                                     (asset "VXX" nil)
                                                     (asset
                                                      "VIXM"
                                                      nil)])])]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "XLP"
                                                      {:window 10})
                                                     75)
                                                    [(group
                                                      "VIX Blend"
                                                      [(weight-equal
                                                        [(asset
                                                          "VIXY"
                                                          nil)
                                                         (asset
                                                          "VXX"
                                                          nil)
                                                         (asset
                                                          "VIXM"
                                                          nil)])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "TQQQ"
                                                          {:window 6})
                                                         -12)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (cumulative-return
                                                              "TQQQ"
                                                              {:window
                                                               1})
                                                             5.5)
                                                            [(group
                                                              "VIX Blend+"
                                                              [(weight-equal
                                                                [(asset
                                                                  "UVXY"
                                                                  nil)
                                                                 (asset
                                                                  "VXX"
                                                                  nil)
                                                                 (asset
                                                                  "VIXM"
                                                                  nil)])])]
                                                            [(group
                                                              "Pops -> KMLM"
                                                              [(weight-equal
                                                                [(if
                                                                  (<
                                                                   (rsi
                                                                    "TQQQ"
                                                                    {:window
                                                                     10})
                                                                   31)
                                                                  [(asset
                                                                    "TECL"
                                                                    nil)]
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
                                                                        nil)]
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
                                                                            nil)]
                                                                          [(group
                                                                            "KMLM Switcher + FNGU"
                                                                            [(weight-equal
                                                                              [(if
                                                                                (>
                                                                                 (rsi
                                                                                  "XLK"
                                                                                  {:window
                                                                                   10})
                                                                                 (rsi
                                                                                  "KMLM"
                                                                                  {:window
                                                                                   10}))
                                                                                [(weight-equal
                                                                                  [(filter
                                                                                    (rsi
                                                                                     {:window
                                                                                      10})
                                                                                    (select-bottom
                                                                                     1)
                                                                                    [(asset
                                                                                      "TECL"
                                                                                      nil)
                                                                                     (asset
                                                                                      "SVXY"
                                                                                      nil)
                                                                                     (group
                                                                                      "50% FNGU / 50% FNGU or Not"
                                                                                      [(weight-equal
                                                                                        [(asset
                                                                                          "FNGU"
                                                                                          nil)
                                                                                         (group
                                                                                          "FNGU or Not"
                                                                                          [(weight-equal
                                                                                            [(filter
                                                                                              (moving-average-return
                                                                                               {:window
                                                                                                20})
                                                                                              (select-top
                                                                                               1)
                                                                                              [(asset
                                                                                                "FNGU"
                                                                                                nil)
                                                                                               (asset
                                                                                                "SPXL"
                                                                                                nil)
                                                                                               (asset
                                                                                                "XLE"
                                                                                                nil)
                                                                                               (asset
                                                                                                "XLK"
                                                                                                nil)
                                                                                               (asset
                                                                                                "AGG"
                                                                                                nil)])])])])])])])]
                                                                                [(weight-equal
                                                                                  [(filter
                                                                                    (stdev-return
                                                                                     {:window
                                                                                      6})
                                                                                    (select-bottom
                                                                                     3)
                                                                                    [(asset
                                                                                      "SVXY"
                                                                                      nil)
                                                                                     (asset
                                                                                      "VIXM"
                                                                                      nil)
                                                                                     (asset
                                                                                      "FTLS"
                                                                                      nil)
                                                                                     (asset
                                                                                      "KMLM"
                                                                                      nil)
                                                                                     (asset
                                                                                      "UUP"
                                                                                      nil)])])])])])])])])])])])])])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (current-price
                                                              "SPY")
                                                             (moving-average-price
                                                              "SPY"
                                                              {:window
                                                               200}))
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (moving-average-price
                                                                  "SPY"
                                                                  {:window
                                                                   3})
                                                                 (moving-average-price
                                                                  "SPY"
                                                                  {:window
                                                                   200}))
                                                                [(group
                                                                  "Bull Cross "
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (rsi
                                                                       {:window
                                                                        10})
                                                                      (select-top
                                                                       2)
                                                                      [(asset
                                                                        "TQQQ"
                                                                        nil)
                                                                       (asset
                                                                        "SPXL"
                                                                        nil)
                                                                       (asset
                                                                        "TMF"
                                                                        nil)])])])]
                                                                [(group
                                                                  "09. Holy Grail | KMLM"
                                                                  [(weight-equal
                                                                    [(if
                                                                      (>
                                                                       (current-price
                                                                        "SPY")
                                                                       (moving-average-price
                                                                        "SPY"
                                                                        {:window
                                                                         200}))
                                                                      [(group
                                                                        "KMLM Switcher + FNGU"
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLK"
                                                                              {:window
                                                                               10})
                                                                             (rsi
                                                                              "KMLM"
                                                                              {:window
                                                                               10}))
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (rsi
                                                                                 {:window
                                                                                  10})
                                                                                (select-bottom
                                                                                 1)
                                                                                [(asset
                                                                                  "TECL"
                                                                                  nil)
                                                                                 (asset
                                                                                  "SVXY"
                                                                                  nil)
                                                                                 (group
                                                                                  "50% FNGU / 50% FNGU or Not"
                                                                                  [(weight-equal
                                                                                    [(asset
                                                                                      "FNGU"
                                                                                      nil)
                                                                                     (group
                                                                                      "FNGU or Not"
                                                                                      [(weight-equal
                                                                                        [(filter
                                                                                          (moving-average-return
                                                                                           {:window
                                                                                            20})
                                                                                          (select-top
                                                                                           1)
                                                                                          [(asset
                                                                                            "FNGU"
                                                                                            nil)
                                                                                           (asset
                                                                                            "SPXL"
                                                                                            nil)
                                                                                           (asset
                                                                                            "XLE"
                                                                                            nil)
                                                                                           (asset
                                                                                            "XLK"
                                                                                            nil)
                                                                                           (asset
                                                                                            "AGG"
                                                                                            nil)])])])])])])])]
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (stdev-return
                                                                                 {:window
                                                                                  6})
                                                                                (select-bottom
                                                                                 3)
                                                                                [(asset
                                                                                  "SVXY"
                                                                                  nil)
                                                                                 (asset
                                                                                  "VIXM"
                                                                                  nil)
                                                                                 (asset
                                                                                  "FTLS"
                                                                                  nil)
                                                                                 (asset
                                                                                  "KMLM"
                                                                                  nil)
                                                                                 (asset
                                                                                  "UUP"
                                                                                  nil)])])])])])]
                                                                      [(weight-equal
                                                                        [(if
                                                                          (<
                                                                           (rsi
                                                                            "QQQ"
                                                                            {:window
                                                                             10})
                                                                           31)
                                                                          [(asset
                                                                            "TECL"
                                                                            nil)]
                                                                          [(weight-equal
                                                                            [(if
                                                                              (<
                                                                               (rsi
                                                                                "SPY"
                                                                                {:window
                                                                                 10})
                                                                               30)
                                                                              [(asset
                                                                                "UPRO"
                                                                                nil)]
                                                                              [(weight-equal
                                                                                [(if
                                                                                  (<
                                                                                   (cumulative-return
                                                                                    "QQQ"
                                                                                    {:window
                                                                                     60})
                                                                                   -12)
                                                                                  [(asset
                                                                                    "BIL"
                                                                                    nil)]
                                                                                  [(weight-equal
                                                                                    [(if
                                                                                      (>
                                                                                       (current-price
                                                                                        "TQQQ")
                                                                                       (moving-average-price
                                                                                        "TQQQ"
                                                                                        {:window
                                                                                         20}))
                                                                                      [(weight-equal
                                                                                        [(if
                                                                                          (<
                                                                                           (rsi
                                                                                            "PSQ"
                                                                                            {:window
                                                                                             10})
                                                                                           32.5)
                                                                                          [(asset
                                                                                            "PSQ"
                                                                                            nil)]
                                                                                          [(group
                                                                                            "KMLM Switcher + FNGU"
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (>
                                                                                                 (rsi
                                                                                                  "XLK"
                                                                                                  {:window
                                                                                                   10})
                                                                                                 (rsi
                                                                                                  "KMLM"
                                                                                                  {:window
                                                                                                   10}))
                                                                                                [(weight-equal
                                                                                                  [(filter
                                                                                                    (rsi
                                                                                                     {:window
                                                                                                      10})
                                                                                                    (select-bottom
                                                                                                     1)
                                                                                                    [(asset
                                                                                                      "TECL"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "SVXY"
                                                                                                      nil)
                                                                                                     (group
                                                                                                      "50% FNGU / 50% FNGU or Not"
                                                                                                      [(weight-equal
                                                                                                        [(asset
                                                                                                          "FNGU"
                                                                                                          nil)
                                                                                                         (group
                                                                                                          "FNGU or Not"
                                                                                                          [(weight-equal
                                                                                                            [(filter
                                                                                                              (moving-average-return
                                                                                                               {:window
                                                                                                                20})
                                                                                                              (select-top
                                                                                                               1)
                                                                                                              [(asset
                                                                                                                "FNGU"
                                                                                                                nil)
                                                                                                               (asset
                                                                                                                "SPXL"
                                                                                                                nil)
                                                                                                               (asset
                                                                                                                "XLE"
                                                                                                                nil)
                                                                                                               (asset
                                                                                                                "XLK"
                                                                                                                nil)
                                                                                                               (asset
                                                                                                                "AGG"
                                                                                                                nil)])])])])])])])]
                                                                                                [(weight-equal
                                                                                                  [(filter
                                                                                                    (stdev-return
                                                                                                     {:window
                                                                                                      6})
                                                                                                    (select-bottom
                                                                                                     3)
                                                                                                    [(asset
                                                                                                      "SVXY"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "VIXM"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "FTLS"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "KMLM"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "UUP"
                                                                                                      nil)])])])])])])])]
                                                                                      [(group
                                                                                        "10/20"
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (>
                                                                                             (rsi
                                                                                              "IEF"
                                                                                              {:window
                                                                                               10})
                                                                                             (rsi
                                                                                              "PSQ"
                                                                                              {:window
                                                                                               20}))
                                                                                            [(asset
                                                                                              "PSQ"
                                                                                              nil)]
                                                                                            [(asset
                                                                                              "QID"
                                                                                              nil)])])])])])])])])])])])])])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (moving-average-price
                                                                  "SPY"
                                                                  {:window
                                                                   3})
                                                                 (moving-average-price
                                                                  "SPY"
                                                                  {:window
                                                                   200}))
                                                                [(group
                                                                  "Bear Cross"
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (rsi
                                                                       {:window
                                                                        10})
                                                                      (select-top
                                                                       2)
                                                                      [(asset
                                                                        "SQQQ"
                                                                        nil)
                                                                       (asset
                                                                        "SPXU"
                                                                        nil)
                                                                       (asset
                                                                        "TMF"
                                                                        nil)
                                                                       (asset
                                                                        "TMV"
                                                                        nil)])])])]
                                                                [(group
                                                                  "09. Holy Grail | KMLM"
                                                                  [(weight-equal
                                                                    [(if
                                                                      (>
                                                                       (current-price
                                                                        "SPY")
                                                                       (moving-average-price
                                                                        "SPY"
                                                                        {:window
                                                                         200}))
                                                                      [(group
                                                                        "KMLM Switcher + FNGU"
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLK"
                                                                              {:window
                                                                               10})
                                                                             (rsi
                                                                              "KMLM"
                                                                              {:window
                                                                               10}))
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (rsi
                                                                                 {:window
                                                                                  10})
                                                                                (select-bottom
                                                                                 1)
                                                                                [(asset
                                                                                  "TECL"
                                                                                  nil)
                                                                                 (asset
                                                                                  "SVXY"
                                                                                  nil)
                                                                                 (group
                                                                                  "50% FNGU / 50% FNGU or Not"
                                                                                  [(weight-equal
                                                                                    [(asset
                                                                                      "FNGU"
                                                                                      nil)
                                                                                     (group
                                                                                      "FNGU or Not"
                                                                                      [(weight-equal
                                                                                        [(filter
                                                                                          (moving-average-return
                                                                                           {:window
                                                                                            20})
                                                                                          (select-top
                                                                                           1)
                                                                                          [(asset
                                                                                            "FNGU"
                                                                                            nil)
                                                                                           (asset
                                                                                            "SPXL"
                                                                                            nil)
                                                                                           (asset
                                                                                            "XLE"
                                                                                            nil)
                                                                                           (asset
                                                                                            "XLK"
                                                                                            nil)
                                                                                           (asset
                                                                                            "AGG"
                                                                                            nil)])])])])])])])]
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (stdev-return
                                                                                 {:window
                                                                                  6})
                                                                                (select-bottom
                                                                                 3)
                                                                                [(asset
                                                                                  "SVXY"
                                                                                  nil)
                                                                                 (asset
                                                                                  "VIXM"
                                                                                  nil)
                                                                                 (asset
                                                                                  "FTLS"
                                                                                  nil)
                                                                                 (asset
                                                                                  "KMLM"
                                                                                  nil)
                                                                                 (asset
                                                                                  "UUP"
                                                                                  nil)])])])])])]
                                                                      [(weight-equal
                                                                        [(if
                                                                          (<
                                                                           (rsi
                                                                            "QQQ"
                                                                            {:window
                                                                             10})
                                                                           31)
                                                                          [(asset
                                                                            "TECL"
                                                                            nil)]
                                                                          [(weight-equal
                                                                            [(if
                                                                              (<
                                                                               (rsi
                                                                                "SPY"
                                                                                {:window
                                                                                 10})
                                                                               30)
                                                                              [(asset
                                                                                "UPRO"
                                                                                nil)]
                                                                              [(weight-equal
                                                                                [(if
                                                                                  (<
                                                                                   (cumulative-return
                                                                                    "QQQ"
                                                                                    {:window
                                                                                     60})
                                                                                   -12)
                                                                                  [(asset
                                                                                    "BIL"
                                                                                    nil)]
                                                                                  [(weight-equal
                                                                                    [(if
                                                                                      (>
                                                                                       (current-price
                                                                                        "TQQQ")
                                                                                       (moving-average-price
                                                                                        "TQQQ"
                                                                                        {:window
                                                                                         20}))
                                                                                      [(weight-equal
                                                                                        [(if
                                                                                          (<
                                                                                           (rsi
                                                                                            "PSQ"
                                                                                            {:window
                                                                                             10})
                                                                                           32.5)
                                                                                          [(asset
                                                                                            "PSQ"
                                                                                            nil)]
                                                                                          [(group
                                                                                            "KMLM Switcher + FNGU"
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (>
                                                                                                 (rsi
                                                                                                  "XLK"
                                                                                                  {:window
                                                                                                   10})
                                                                                                 (rsi
                                                                                                  "KMLM"
                                                                                                  {:window
                                                                                                   10}))
                                                                                                [(weight-equal
                                                                                                  [(filter
                                                                                                    (rsi
                                                                                                     {:window
                                                                                                      10})
                                                                                                    (select-bottom
                                                                                                     1)
                                                                                                    [(asset
                                                                                                      "TECL"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "SVXY"
                                                                                                      nil)
                                                                                                     (group
                                                                                                      "50% FNGU / 50% FNGU or Not"
                                                                                                      [(weight-equal
                                                                                                        [(asset
                                                                                                          "FNGU"
                                                                                                          nil)
                                                                                                         (group
                                                                                                          "FNGU or Not"
                                                                                                          [(weight-equal
                                                                                                            [(filter
                                                                                                              (moving-average-return
                                                                                                               {:window
                                                                                                                20})
                                                                                                              (select-top
                                                                                                               1)
                                                                                                              [(asset
                                                                                                                "FNGU"
                                                                                                                nil)
                                                                                                               (asset
                                                                                                                "SPXL"
                                                                                                                nil)
                                                                                                               (asset
                                                                                                                "XLE"
                                                                                                                nil)
                                                                                                               (asset
                                                                                                                "XLK"
                                                                                                                nil)
                                                                                                               (asset
                                                                                                                "AGG"
                                                                                                                nil)])])])])])])])]
                                                                                                [(weight-equal
                                                                                                  [(filter
                                                                                                    (stdev-return
                                                                                                     {:window
                                                                                                      6})
                                                                                                    (select-bottom
                                                                                                     3)
                                                                                                    [(asset
                                                                                                      "SVXY"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "VIXM"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "FTLS"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "KMLM"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "UUP"
                                                                                                      nil)])])])])])])])]
                                                                                      [(group
                                                                                        "10/20"
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (>
                                                                                             (rsi
                                                                                              "IEF"
                                                                                              {:window
                                                                                               10})
                                                                                             (rsi
                                                                                              "PSQ"
                                                                                              {:window
                                                                                               20}))
                                                                                            [(asset
                                                                                              "PSQ"
                                                                                              nil)]
                                                                                            [(asset
                                                                                              "QID"
                                                                                              nil)])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
     (group
      "410/38 (11) - MonkeyBusiness Simons variant"
      [(weight-equal
        [(group
          "KMLM switcher (single pops)| BT 4/13/22 = A.R. 466% / D.D. 22%"
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
                                               (rsi "XLY" {:window 10})
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
                                                        [(group
                                                          "Single Popped KMLM"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (rsi
                                                                "UVXY"
                                                                {:window
                                                                 21})
                                                               65)
                                                              [(weight-equal
                                                                [(group
                                                                  "BSC"
                                                                  [(weight-equal
                                                                    [(if
                                                                      (>
                                                                       (rsi
                                                                        "SPY"
                                                                        {:window
                                                                         21})
                                                                       30)
                                                                      [(asset
                                                                        "VIXM"
                                                                        "ProShares VIX Mid-Term Futures ETF")]
                                                                      [(asset
                                                                        "SPXL"
                                                                        "Direxion Daily S&P 500 Bull 3x Shares")])])])])]
                                                              [(weight-equal
                                                                [(group
                                                                  "Combined Pop Bot"
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
                                                                                  "Copypasta YOLO GainZs Here"
                                                                                  [(weight-equal
                                                                                    [(group
                                                                                      "KMLM switcher: TECL, SVIX, or L/S Rotator | BT 4/13/22 = AR 164% / DD 22.2%"
                                                                                      [(weight-equal
                                                                                        [(if
                                                                                          (>
                                                                                           (rsi
                                                                                            "XLK"
                                                                                            {:window
                                                                                             10})
                                                                                           (rsi
                                                                                            "KMLM"
                                                                                            {:window
                                                                                             10}))
                                                                                          [(weight-equal
                                                                                            [(filter
                                                                                              (rsi
                                                                                               {:window
                                                                                                10})
                                                                                              (select-bottom
                                                                                               1)
                                                                                              [(asset
                                                                                                "FNGU"
                                                                                                "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                                                          [(group
                                                                                            "Long/Short Rotator with FTLS KMLM SSO UUP | BT 12/10/20 | 15.1/3.5  "
                                                                                            [(weight-equal
                                                                                              [(filter
                                                                                                (stdev-return
                                                                                                 {:window
                                                                                                  6})
                                                                                                (select-bottom
                                                                                                 1)
                                                                                                [(asset
                                                                                                  "UUP"
                                                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                                                 (asset
                                                                                                  "FTLS"
                                                                                                  "First Trust Long/Short Equity ETF")
                                                                                                 (asset
                                                                                                  "KMLM"
                                                                                                  "KFA Mount Lucas Managed Futures Index Strategy ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
     (group
      "Nerfed 2900/8 (373) - Nova - Short BT (remove for longer backtest)"
      [(weight-equal
        [(group
          "KMLM switcher (single pops)| BT 4/13/22 = A.R. 466% / D.D. 22%"
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
                                               (rsi "XLY" {:window 10})
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
                                                        [(group
                                                          "Single Popped KMLM"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (rsi
                                                                "UVIX"
                                                                {:window
                                                                 21})
                                                               65)
                                                              [(weight-equal
                                                                [(group
                                                                  "BSC"
                                                                  [(weight-equal
                                                                    [(if
                                                                      (>
                                                                       (rsi
                                                                        "SPY"
                                                                        {:window
                                                                         21})
                                                                       30)
                                                                      [(asset
                                                                        "VIXM"
                                                                        "ProShares VIX Mid-Term Futures ETF")]
                                                                      [(asset
                                                                        "SPXL"
                                                                        "Direxion Daily S&P 500 Bull 3x Shares")])])])])]
                                                              [(weight-equal
                                                                [(group
                                                                  "Combined Pop Bot"
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
                                                                                  "Copypasta YOLO GainZs Here"
                                                                                  [(weight-equal
                                                                                    [(group
                                                                                      "KMLM switcher: TECL, SVIX, or L/S Rotator | BT 4/13/22 = AR 164% / DD 22.2%"
                                                                                      [(weight-equal
                                                                                        [(if
                                                                                          (>
                                                                                           (rsi
                                                                                            "XLK"
                                                                                            {:window
                                                                                             10})
                                                                                           (rsi
                                                                                            "KMLM"
                                                                                            {:window
                                                                                             10}))
                                                                                          [(weight-equal
                                                                                            [(filter
                                                                                              (rsi
                                                                                               {:window
                                                                                                11})
                                                                                              (select-top
                                                                                               1)
                                                                                              [(asset
                                                                                                "FNGO"
                                                                                                "MicroSectors FANG+ Index 2X Leveraged ETNs")
                                                                                               (asset
                                                                                                "TSLA"
                                                                                                "Tesla, Inc.")
                                                                                               (asset
                                                                                                "MSFT"
                                                                                                "Microsoft Corporation")
                                                                                               (asset
                                                                                                "AAPL"
                                                                                                "Apple Inc.")
                                                                                               (asset
                                                                                                "NVDA"
                                                                                                "NVIDIA Corporation")
                                                                                               (asset
                                                                                                "GOOGL"
                                                                                                "Alphabet Inc. Class A")
                                                                                               (asset
                                                                                                "AMZN"
                                                                                                "Amazon.com, Inc.")])])]
                                                                                          [(group
                                                                                            "Long/Short Rotator with FTLS KMLM SSO UUP | BT 12/10/20 | 15.1/3.5  "
                                                                                            [(weight-equal
                                                                                              [(filter
                                                                                                (stdev-return
                                                                                                 {:window
                                                                                                  6})
                                                                                                (select-bottom
                                                                                                 1)
                                                                                                [(asset
                                                                                                  "UUP"
                                                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                                                 (asset
                                                                                                  "FTLS"
                                                                                                  "First Trust Long/Short Equity ETF")
                                                                                                 (asset
                                                                                                  "KMLM"
                                                                                                  "KFA Mount Lucas Managed Futures Index Strategy ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
     (group
      "830/21 (39) MonkeyBusiness Simons variant V2"
      [(weight-equal
        [(group
          "KMLM switcher | Simon Shorts Ed. + MbM | (single pops)| BT 4/13/22 "
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
                                               (rsi "XLY" {:window 10})
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
                                                        [(group
                                                          "Single Popped KMLM"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (rsi
                                                                "UVXY"
                                                                {:window
                                                                 21})
                                                               65)
                                                              [(weight-equal
                                                                [(group
                                                                  "BSC"
                                                                  [(weight-equal
                                                                    [(if
                                                                      (>
                                                                       (rsi
                                                                        "SPY"
                                                                        {:window
                                                                         21})
                                                                       30)
                                                                      [(asset
                                                                        "VIXM"
                                                                        "ProShares VIX Mid-Term Futures ETF")]
                                                                      [(asset
                                                                        "SPXL"
                                                                        "Direxion Daily S&P 500 Bull 3x Shares")])])])])]
                                                              [(weight-equal
                                                                [(group
                                                                  "Combined Pop Bot"
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
                                                                                  "Copypasta YOLO GainZs Here"
                                                                                  [(weight-equal
                                                                                    [(group
                                                                                      "KMLM switcher: TECL, SVIX, or L/S Rotator | BT 4/13/22 = AR 164% / DD 22.2%"
                                                                                      [(weight-equal
                                                                                        [(if
                                                                                          (>
                                                                                           (rsi
                                                                                            "XLK"
                                                                                            {:window
                                                                                             10})
                                                                                           (rsi
                                                                                            "KMLM"
                                                                                            {:window
                                                                                             10}))
                                                                                          [(weight-equal
                                                                                            [(filter
                                                                                              (rsi
                                                                                               {:window
                                                                                                10})
                                                                                              (select-top
                                                                                               1)
                                                                                              [(asset
                                                                                                "TECL"
                                                                                                "Direxion Daily Technology Bull 3x Shares")
                                                                                               (asset
                                                                                                "SOXL"
                                                                                                "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                               (asset
                                                                                                "SVIX"
                                                                                                "-1x Short VIX Futures ETF")])])]
                                                                                          [(weight-equal
                                                                                            [(group
                                                                                              "Bond Check --> Shorts, Bonds, KMLM, SPLV"
                                                                                              [(weight-equal
                                                                                                [(if
                                                                                                  (>
                                                                                                   (moving-average-return
                                                                                                    "BND"
                                                                                                    {:window
                                                                                                     20})
                                                                                                   0)
                                                                                                  [(weight-equal
                                                                                                    [(filter
                                                                                                      (rsi
                                                                                                       {:window
                                                                                                        10})
                                                                                                      (select-bottom
                                                                                                       1)
                                                                                                      [(asset
                                                                                                        "KMLM"
                                                                                                        "KFA Mount Lucas Managed Futures Index Strategy ETF")
                                                                                                       (asset
                                                                                                        "SPLV"
                                                                                                        "Invesco S&P 500 Low Volatility ETF")])])]
                                                                                                  [(weight-equal
                                                                                                    [(filter
                                                                                                      (rsi
                                                                                                       {:window
                                                                                                        10})
                                                                                                      (select-top
                                                                                                       1)
                                                                                                      [(asset
                                                                                                        "TLT"
                                                                                                        "iShares 20+ Year Treasury Bond ETF")
                                                                                                       (asset
                                                                                                        "LABD"
                                                                                                        "Direxion Daily S&P Biotech Bear 3X Shares")
                                                                                                       (asset
                                                                                                        "TZA"
                                                                                                        "Direxion Daily Small Cap Bear 3x Shares")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]))
