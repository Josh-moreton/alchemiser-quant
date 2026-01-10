(defsymphony
 "Flextiger-DefAI+eVTOL v1 7dRSI Top2|7/24 (public copy)"
 {:asset-class "EQUITIES", :rebalance-threshold 0.05}
 (weight-equal
  [(group
    "Flextiger AI Defense+eVTOL V1 7dRSI Top2/Jul 23, 2025 {www.patreon.com/Flextiger}"
    [(weight-equal
      [(filter
        (rsi {:window 7})
        (select-top 2)
        [(asset "AIRO" "AIRO Group Holdings Inc.")
         (asset "BBAI" "BigBear.ai Holdings Inc")
         (asset "KTOS" "Kratos Defense & Security Solutions Inc")
         (asset "ONDS" "Ondas Holdings Inc")
         (asset "OSS" "One Stop Systems Inc")
         (asset "RCAT" "Red Cat Holdings Inc")
         (asset "SPAI" "Safe Pro Group Inc")
         (asset "UMAC" "Unusual Machines Inc")
         (asset
          "ITA"
          "BlackRock Institutional Trust Company N.A. - iShares U.S. Aerospace & Defense ETF")
         (asset
          "ACHR"
          "Archer Aviation Inc - Ordinary Shares - Class A")
         (asset "EVTL" "Vertical Aerospace Ltd")
         (asset "JOBY" "Joby Aviation Inc")])])])]))
