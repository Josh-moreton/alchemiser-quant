(defsymphony
 "Rain's Concise EM Leverage -> Leveraged Sectors"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "Rain's Concise EM Leverage -> Leveraged Sectors"
    [(weight-equal
      [(if
        (< (rsi "EEM" {:window 14}) 30)
        [(asset "EDC" nil)]
        [(if
          (> (rsi "EEM" {:window 10}) 80)
          [(asset "EDZ" nil)]
          [(if
            (>
             (current-price "SHV")
             (moving-average-price "SHV" {:window 50}))
            [(if
              (>
               (current-price "EEM")
               (moving-average-price "EEM" {:window 200}))
              [(if
                (> (rsi "MMT" {:window 10}) (rsi "XLU" {:window 10}))
                [(if
                  (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IEI" {:window 10})
                       (rsi "IWM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(asset "EDC" nil)]
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(weight-equal
                          [(asset "EDZ" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])])])]
                    [(if
                      (>
                       (rsi "IEI" {:window 10})
                       (rsi "IWM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(weight-equal
                          [(asset "EDC" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])]
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(asset "EDZ" nil)])])])])]
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IEI" {:window 10})
                       (rsi "IWM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(weight-equal
                          [(asset "EDC" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])]
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(asset "EDZ" nil)])])])]
                    [(if
                      (>
                       (rsi "IEI" {:window 10})
                       (rsi "IWM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(asset "EDZ" nil)])])])])]
                [(if
                  (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IEI" {:window 10})
                       (rsi "IWM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(weight-equal
                          [(asset "EDC" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])]
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(asset "EDZ" nil)])])])]
                    [(if
                      (>
                       (rsi "IEI" {:window 10})
                       (rsi "IWM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(asset "EDZ" nil)])])])]
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IEI" {:window 10})
                       (rsi "IWM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(asset "EDZ" nil)])])]
                    [(if
                      (>
                       (rsi "IEI" {:window 10})
                       (rsi "IWM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(if
                          (>
                           (rsi "IEF" {:window 10})
                           (rsi "DIA" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(weight-equal
                          [(asset "EDZ" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DBE" {:window 10}))
                        [(weight-equal
                          [(asset "EDZ" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(asset "EDZ" nil)])])])])])]
              [(if
                (> (rsi "MMT" {:window 10}) (rsi "XLU" {:window 10}))
                [(if
                  (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IGIB" {:window 15})
                       (rsi "EEM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(asset "EDC" nil)]
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])])])]
                    [(if
                      (>
                       (rsi "IGIB" {:window 15})
                       (rsi "EEM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(asset "EDC" nil)]
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(asset "EDZ" nil)])])])])]
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IGIB" {:window 15})
                       (rsi "EEM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(asset "EDC" nil)]
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(asset "EDZ" nil)])])])]
                    [(if
                      (>
                       (rsi "IGIB" {:window 15})
                       (rsi "EEM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(asset "EDZ" nil)])])])])])]
                [(if
                  (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IGIB" {:window 15})
                       (rsi "EEM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(asset "EDC" nil)]
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(asset "EDZ" nil)])])])]
                    [(if
                      (>
                       (rsi "IGIB" {:window 15})
                       (rsi "EEM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(asset "EDZ" nil)])])])])]
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IGIB" {:window 15})
                       (rsi "EEM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(asset "EDZ" nil)])])])]
                    [(if
                      (>
                       (rsi "IGIB" {:window 15})
                       (rsi "EEM" {:window 15}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(asset "EDZ" nil)])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(asset "EDZ" nil)])])])])])])])]
            [(if
              (>
               (current-price "EEM")
               (moving-average-price "EEM" {:window 200}))
              [(if
                (> (rsi "MMT" {:window 10}) (rsi "XLU" {:window 10}))
                [(if
                  (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "DBE" {:window 10}))
                      [(if
                        (>
                         (rsi "IEF" {:window 10})
                         (rsi "DIA" {:window 10}))
                        [(asset "EDC" nil)]
                        [(weight-equal
                          [(asset "EDC" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])])]
                      [(if
                        (>
                         (rsi "IEF" {:window 10})
                         (rsi "DIA" {:window 10}))
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])]
                        [(weight-equal
                          [(asset "EDZ" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])])])]
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "DBE" {:window 10}))
                      [(if
                        (>
                         (rsi "IEF" {:window 10})
                         (rsi "DIA" {:window 10}))
                        [(weight-equal
                          [(asset "EDC" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])])]
                      [(weight-equal
                        [(asset "EDZ" nil)
                         (group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])])])])]
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "DBE" {:window 10}))
                      [(if
                        (>
                         (rsi "IEF" {:window 10})
                         (rsi "DIA" {:window 10}))
                        [(weight-equal
                          [(asset "EDC" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])])]
                      [(weight-equal
                        [(asset "EDZ" nil)
                         (group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])])])]
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "DBE" {:window 10}))
                      [(if
                        (>
                         (rsi "IEF" {:window 10})
                         (rsi "DIA" {:window 10}))
                        [(weight-equal
                          [(asset "EDC" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])])]
                      [(asset "EDZ" nil)])])])]
                [(if
                  (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "DBE" {:window 10}))
                      [(if
                        (>
                         (rsi "IEF" {:window 10})
                         (rsi "DIA" {:window 10}))
                        [(weight-equal
                          [(asset "EDC" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])])]
                      [(weight-equal
                        [(asset "EDZ" nil)
                         (group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])])])]
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "DBE" {:window 10}))
                      [(if
                        (>
                         (rsi "IEF" {:window 10})
                         (rsi "DIA" {:window 10}))
                        [(weight-equal
                          [(asset "EDC" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])])]
                      [(asset "EDZ" nil)])])]
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "DBE" {:window 10}))
                      [(if
                        (>
                         (rsi "IEF" {:window 10})
                         (rsi "DIA" {:window 10}))
                        [(weight-equal
                          [(asset "EDC" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])])]
                      [(asset "EDZ" nil)])]
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "DBE" {:window 10}))
                      [(if
                        (>
                         (rsi "IEF" {:window 10})
                         (rsi "DIA" {:window 10}))
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])]
                        [(weight-equal
                          [(asset "EDZ" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])])]
                      [(asset "EDZ" nil)])])])])]
              [(if
                (> (rsi "MMT" {:window 10}) (rsi "XLU" {:window 10}))
                [(if
                  (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "SPY" {:window 10}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(asset "EDC" nil)]
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])])])]
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "SPY" {:window 10}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(asset "EDC" nil)]
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(asset "EDZ" nil)])])])])]
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "SPY" {:window 10}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(asset "EDC" nil)]
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(asset "EDZ" nil)])])])]
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "SPY" {:window 10}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(asset "EDZ" nil)])])])])])]
                [(if
                  (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
                  [(if
                    (>
                     (rsi "MHD" {:window 10})
                     (rsi "XLP" {:window 10}))
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "SPY" {:window 10}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(asset "EDC" nil)]
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(asset "EDZ" nil)])])])]
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "SPY" {:window 10}))
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDC" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])])]
                      [(if
                        (>
                         (rsi "IGIB" {:window 10})
                         (rsi "DLN" {:window 10}))
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])]
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])])]
                        [(if
                          (>
                           (rsi "ISCB" {:window 10})
                           (rsi "IWM" {:window 10}))
                          [(weight-equal
                            [(asset "EDZ" nil)
                             (group
                              "Leveraged Sectors or Bonds"
                              [(weight-equal
                                [(filter
                                  (rsi {:window 10})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])
                                 (filter
                                  (rsi {:window 6})
                                  (select-bottom 1)
                                  [(asset "TMF" nil)
                                   (asset "CURE" nil)
                                   (asset "DRN" nil)
                                   (asset "ROM" nil)
                                   (asset "VBF" nil)
                                   (asset "EVN" nil)
                                   (asset "BKT" nil)
                                   (asset "PMM" nil)
                                   (asset "XLF" nil)])])])])]
                          [(asset "EDZ" nil)])])])])]
                  [(if
                    (>
                     (rsi "IGIB" {:window 10})
                     (rsi "SPY" {:window 10}))
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "DLN" {:window 10}))
                      [(if
                        (>
                         (rsi "ISCB" {:window 10})
                         (rsi "IWM" {:window 10}))
                        [(weight-equal
                          [(asset "EDC" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])])]
                      [(if
                        (>
                         (rsi "ISCB" {:window 10})
                         (rsi "IWM" {:window 10}))
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])]
                        [(weight-equal
                          [(asset "EDZ" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])])])]
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "DLN" {:window 10}))
                      [(if
                        (>
                         (rsi "ISCB" {:window 10})
                         (rsi "IWM" {:window 10}))
                        [(group
                          "Leveraged Sectors or Bonds"
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])
                             (filter
                              (rsi {:window 6})
                              (select-bottom 1)
                              [(asset "TMF" nil)
                               (asset "CURE" nil)
                               (asset "DRN" nil)
                               (asset "ROM" nil)
                               (asset "VBF" nil)
                               (asset "EVN" nil)
                               (asset "BKT" nil)
                               (asset "PMM" nil)
                               (asset "XLF" nil)])])])]
                        [(weight-equal
                          [(asset "EDZ" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])])]
                      [(if
                        (>
                         (rsi "ISCB" {:window 10})
                         (rsi "IWM" {:window 10}))
                        [(weight-equal
                          [(asset "EDZ" nil)
                           (group
                            "Leveraged Sectors or Bonds"
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])
                               (filter
                                (rsi {:window 6})
                                (select-bottom 1)
                                [(asset "TMF" nil)
                                 (asset "CURE" nil)
                                 (asset "DRN" nil)
                                 (asset "ROM" nil)
                                 (asset "VBF" nil)
                                 (asset "EVN" nil)
                                 (asset "BKT" nil)
                                 (asset "PMM" nil)
                                 (asset "XLF" nil)])])])])]
                        [(asset "EDZ" nil)])])])])])])])])])])])]))
