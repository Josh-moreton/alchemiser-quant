(defsymphony
 "LQQ3 or XSPS KMLM Phenomenon (UK adapted)"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "LQQ3 or XSPS KMLM Phenomenon"
    [(weight-equal
      [(if
        (> (rsi "IEF" {:window 20}) (rsi "PSQ" {:window 20}))
        [(weight-equal
          [(if
            (> (rsi "XLK" {:window 10}) (rsi "KMLM" {:window 10}))
            [(asset
              "LQQ3"
              "3x Long Leveraged Nasdaq 100 ETF (UK)")]
            [(weight-equal
              [(if
                (> (rsi "XLK" {:window 10}) (rsi "DBMF" {:window 10}))
                [(weight-equal
                  [(asset
                    "XSPS"
                    "Short S&P 500 ETF (UK)")])]
                [(weight-equal
                  [(asset
                    "XSPS"
                    "Short S&P 500 ETF (UK)")])])])])])]
        [(weight-equal
          [(if
            (< (rsi "LQQ3" {:window 10}) 31)
            [(asset
              "LQQ3"
              "3x Long Leveraged Nasdaq 100 ETF (UK)")]
            [(weight-equal
              [(if
                (> (rsi "XLK" {:window 10}) (rsi "DBMF" {:window 10}))
                [(weight-equal
                  [(asset
                    "XSPS"
                    "Short S&P 500 ETF (UK)")])]
                [(weight-equal
                  [(asset
                    "XSPS"
                    "Short S&P 500 ETF (UK)")])])])])])])])])]))
