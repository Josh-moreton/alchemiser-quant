(defsymphony
 "FOMO NOMO - No Leverage"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
    (> (current-price "VTI") (moving-average-price "VTI" {:window 60}))
    [(weight-equal
      [(if
        (>
         (current-price "MTUM")
         (moving-average-price "MTUM" {:window 150}))
        [(weight-equal
          [(group
            "Top 300 Combined Sharpe (6mo) Unleveraged"
            [(weight-equal
              [(filter
                (cumulative-return {:window 2})
                (select-top 5)
                [(asset "HYMC" "")
                 (asset "NUAI" "")
                 (asset "SNDK" "")
                 (asset "BW" "")
                 (asset "SATS" "")
                 (asset "AXTI" "")
                 (asset "RLMD" "")
                 (asset "HL" "")
                 (asset "STTK" "")
                 (asset "ANRO" "")
                 (asset "ERAS" "")
                 (asset "TE" "")
                 (asset "PRAX" "")
                 (asset "VICR" "")
                 (asset "IAUX" "")
                 (asset "XWIN" "")
                 (asset "ASYS" "")
                 (asset "ONDS" "")
                 (asset "TTI" "")
                 (asset "CGAU" "")
                 (asset "TRX" "")
                 (asset "MU" "")
                 (asset "B" "")
                 (asset "ARWR" "")
                 (asset "PL" "")
                 (asset "ARMN" "")
                 (asset "IRWD" "")
                 (asset "COPJ" "")
                 (asset "TMQ" "")
                 (asset "CELC" "")
                 (asset "IAG" "")
                 (asset "SIVR" "")
                 (asset "ERO" "")
                 (asset "SLV" "")
                 (asset "VTYX" "")
                 (asset "DRD" "")
                 (asset "USAS" "")
                 (asset "NESR" "")
                 (asset "ZURA" "")
                 (asset "SLVP" "")
                 (asset "AUGO" "")
                 (asset "SPHR" "")
                 (asset "SILJ" "")
                 (asset "WDC" "")
                 (asset "HBM" "")
                 (asset "NEO" "")
                 (asset "NRGV" "")
                 (asset "EGO" "")
                 (asset "BIOA" "")
                 (asset "MAZE" "")
                 (asset "COPX" "")
                 (asset "EQX" "")
                 (asset "SIL" "")
                 (asset "NGD" "")
                 (asset "PSLV" "")
                 (asset "WBD" "")
                 (asset "ALB" "")
                 (asset "WRN" "")
                 (asset "NAK" "")
                 (asset "GDXJ" "")
                 (asset "IONS" "")
                 (asset "SVM" "")
                 (asset "TSEM" "")
                 (asset "TROO" "")
                 (asset "BE" "")
                 (asset "NEXA" "")
                 (asset "CSTL" "")
                 (asset "ROIV" "")
                 (asset "KGC" "")
                 (asset "INBX" "")
                 (asset "AG" "")
                 (asset "SLVR" "")
                 (asset "EFXT" "")
                 (asset "PEPG" "")
                 (asset "GLUE" "")
                 (asset "GLTR" "")
                 (asset "CRML" "")
                 (asset "APLD" "")
                 (asset "RAPT" "")
                 (asset "BTSG" "")
                 (asset "NVA" "")
                 (asset "JMIA" "")
                 (asset "VSCO" "")
                 (asset "ITRG" "")
                 (asset "RGLD" "")
                 (asset "CDE" "")
                 (asset "MUX" "")
                 (asset "GILT" "")
                 (asset "CEF" "")
                 (asset "GDX" "")
                 (asset "ALM" "")
                 (asset "SETM" "")
                 (asset "BVN" "")
                 (asset "RING" "")
                 (asset "LRCX" "")
                 (asset "TERN" "")
                 (asset "VISN" "")
                 (asset "LPTH" "")
                 (asset "ALMS" "")
                 (asset "VSAT" "")
                 (asset "SCCO" "")
                 (asset "GOLD" "")
                 (asset "TER" "")
                 (asset "LAR" "")
                 (asset "OVID" "")
                 (asset "BTU" "")
                 (asset "ASML" "")
                 (asset "ASM" "")
                 (asset "HP" "")
                 (asset "KOD" "")
                 (asset "NTRA" "")
                 (asset "ATRO" "")
                 (asset "COPP" "")
                 (asset "IREN" "")
                 (asset "SQM" "")
                 (asset "ASX" "")
                 (asset "CIEN" "")
                 (asset "TGB" "")
                 (asset "AAUC" "")
                 (asset "TYRA" "")
                 (asset "BLTE" "")
                 (asset "GH" "")
                 (asset "KSLV" "")
                 (asset "GRAL" "")
                 (asset "KRYS" "")
                 (asset "VGZ" "")
                 (asset "FTAI" "")
                 (asset "MTA" "")
                 (asset "MKSI" "")
                 (asset "ORKA" "")
                 (asset "AU" "")
                 (asset "PAAS" "")
                 (asset "SII" "")
                 (asset "NEM" "")
                 (asset "PGEN" "")
                 (asset "INDV" "")
                 (asset "VRDN" "")
                 (asset "GLDG" "")
                 (asset "FLNC" "")
                 (asset "NGL" "")
                 (asset "GFI" "")
                 (asset "SSRM" "")
                 (asset "AXGN" "")
                 (asset "HLIO" "")
                 (asset "SKE" "")
                 (asset "MRCY" "")
                 (asset "MLYS" "")
                 (asset "AVAH" "")
                 (asset "REMX" "")
                 (asset "AMRX" "")
                 (asset "ONTO" "")
                 (asset "NG" "")
                 (asset "RVMD" "")
                 (asset "CMTL" "")
                 (asset "FLKR" "")
                 (asset "BKD" "")
                 (asset "EWY" "")
                 (asset "XME" "")
                 (asset "AREC" "")
                 (asset "MIRM" "")
                 (asset "AVDL" "")
                 (asset "CTNM" "")
                 (asset "ELAN" "")
                 (asset "REAL" "")
                 (asset "IPSC" "")
                 (asset "BORR" "")
                 (asset "RCUS" "")
                 (asset "EXK" "")
                 (asset "GM" "")
                 (asset "SBSW" "")
                 (asset "LITE" "")
                 (asset "CIFR" "")
                 (asset "TEVA" "")
                 (asset "FOLD" "")
                 (asset "CNTX" "")
                 (asset "SA" "")
                 (asset "AVTX" "")
                 (asset "WULF" "")
                 (asset "EMBJ" "")
                 (asset "CMI" "")
                 (asset "EZPW" "")
                 (asset "LQDA" "")
                 (asset "HUT" "")
                 (asset "AEO" "")
                 (asset "FTRE" "")
                 (asset "NBP" "")
                 (asset "TCMD" "")
                 (asset "TARS" "")
                 (asset "RLAY" "")
                 (asset "DAN" "")
                 (asset "FBRX" "")
                 (asset "DNTH" "")
                 (asset "CCO" "")
                 (asset "MOFG" "")
                 (asset "HTHT" "")
                 (asset "NEWP" "")
                 (asset "ANNX" "")
                 (asset "GPCR" "")
                 (asset "STX" "")
                 (asset "STOK" "")
                 (asset "DSGN" "")
                 (asset "SVRA" "")
                 (asset "LAC" "")
                 (asset "CYTK" "")
                 (asset "HII" "")
                 (asset "CHRW" "")
                 (asset "LASR" "")
                 (asset "APGE" "")
                 (asset "MSGE" "")
                 (asset "TECK" "")
                 (asset "VFF" "")
                 (asset "UPB" "")
                 (asset "GAU" "")
                 (asset "GSAT" "")
                 (asset "AEM" "")
                 (asset "OR" "")
                 (asset "SNDX" "")
                 (asset "OPEN" "")
                 (asset "AA" "")
                 (asset "LTRX" "")
                 (asset "KLAC" "")
                 (asset "KALU" "")
                 (asset "DOCN" "")
                 (asset "CTMX" "")
                 (asset "TPC" "")
                 (asset "KRMN" "")
                 (asset "WNTR" "")
                 (asset "VREX" "")
                 (asset "UUUU" "")
                 (asset "CENX" "")
                 (asset "ALHC" "")
                 (asset "SYRE" "")
                 (asset "PPTA" "")
                 (asset "CDZI" "")
                 (asset "SKYT" "")
                 (asset "AMAT" "")
                 (asset "IMNM" "")
                 (asset "DHC" "")
                 (asset "AMRC" "")
                 (asset "NIKL" "")
                 (asset "RERE" "")
                 (asset "GGB" "")
                 (asset "RYAM" "")
                 (asset "CECO" "")
                 (asset "CLB" "")
                 (asset "AGI" "")
                 (asset "THM" "")
                 (asset "VIAV" "")
                 (asset "SHMD" "")
                 (asset "CLYM" "")
                 (asset "REPL" "")
                 (asset "TENX" "")
                 (asset "TPB" "")
                 (asset "WPM" "")
                 (asset "NBR" "")
                 (asset "SHOO" "")
                 (asset "FSM" "")
                 (asset "ESPR" "")
                 (asset "VZLA" "")
                 (asset "VERA" "")
                 (asset "TFPM" "")
                 (asset "RIG" "")
                 (asset "NB" "")
                 (asset "UAMY" "")
                 (asset "CMPX" "")
                 (asset "EXAS" "")
                 (asset "COMP" "")
                 (asset "INTC" "")
                 (asset "NVRI" "")
                 (asset "ZUMZ" "")
                 (asset "KLIC" "")
                 (asset "GPGI" "")
                 (asset "XPEL" "")
                 (asset "SION" "")
                 (asset "GMAB" "")
                 (asset "SLI" "")
                 (asset "ANAB" "")
                 (asset "GLW" "")
                 (asset "CSTM" "")
                 (asset "VOXR" "")
                 (asset "AXSM" "")
                 (asset "APH" "")
                 (asset "HAL" "")
                 (asset "AUPH" "")
                 (asset "SXI" "")
                 (asset "BIDU" "")
                 (asset "DBVT" "")
                 (asset "NU" "")
                 (asset "FORM" "")
                 (asset "GLSI" "")
                 (asset "POWL" "")
                 (asset "OLMA" "")
                 (asset "EOSE" "")
                 (asset "CGON" "")
                 (asset "CX" "")
                 (asset "WFRD" "")
                 (asset "BSBR" "")
                 (asset "NVMI" "")
                 (asset "OMCL" "")])])])
           (group
            "Top 300 Combined Sharpe (3mo) Unleveraged"
            [(weight-equal
              [(filter
                (cumulative-return {:window 2})
                (select-top 5)
                [(asset "HYMC" "")
                 (asset "ERAS" "")
                 (asset "NEXA" "")
                 (asset "SIVR" "")
                 (asset "SLV" "")
                 (asset "KSLV" "")
                 (asset "ARMN" "")
                 (asset "EGO" "")
                 (asset "PSLV" "")
                 (asset "ALMS" "")
                 (asset "IPSC" "")
                 (asset "SKE" "")
                 (asset "AUGO" "")
                 (asset "SQM" "")
                 (asset "IAUX" "")
                 (asset "SVM" "")
                 (asset "GLTR" "")
                 (asset "COPJ" "")
                 (asset "RGLD" "")
                 (asset "BW" "")
                 (asset "ASYS" "")
                 (asset "SLVP" "")
                 (asset "CEF" "")
                 (asset "CGAU" "")
                 (asset "BVN" "")
                 (asset "GLSI" "")
                 (asset "ALB" "")
                 (asset "LCII" "")
                 (asset "SLVR" "")
                 (asset "TGB" "")
                 (asset "TERN" "")
                 (asset "HL" "")
                 (asset "SIL" "")
                 (asset "SII" "")
                 (asset "IRWD" "")
                 (asset "ERO" "")
                 (asset "SBSW" "")
                 (asset "B" "")
                 (asset "PAAS" "")
                 (asset "GOLD" "")
                 (asset "USAS" "")
                 (asset "SILJ" "")
                 (asset "WPM" "")
                 (asset "GDXJ" "")
                 (asset "COPX" "")
                 (asset "NGD" "")
                 (asset "ALTO" "")
                 (asset "TYRA" "")
                 (asset "FCX" "")
                 (asset "ASM" "")
                 (asset "GDX" "")
                 (asset "BKD" "")
                 (asset "IAG" "")
                 (asset "VICR" "")
                 (asset "NEM" "")
                 (asset "TRX" "")
                 (asset "FBRX" "")
                 (asset "RING" "")
                 (asset "AG" "")
                 (asset "COPP" "")
                 (asset "HLF" "")
                 (asset "OMCL" "")
                 (asset "AXTI" "")
                 (asset "BIOA" "")
                 (asset "AAUC" "")
                 (asset "TEVA" "")
                 (asset "LQDA" "")
                 (asset "KGC" "")
                 (asset "WRN" "")
                 (asset "AU" "")
                 (asset "MATX" "")
                 (asset "SNDK" "")
                 (asset "HBM" "")
                 (asset "THR" "")
                 (asset "AXGN" "")
                 (asset "CSTL" "")
                 (asset "COMP" "")
                 (asset "SATL" "")
                 (asset "XPEL" "")
                 (asset "SATS" "")
                 (asset "ORLA" "")
                 (asset "SCCO" "")
                 (asset "NEWP" "")
                 (asset "ASX" "")
                 (asset "KRYS" "")
                 (asset "SETM" "")
                 (asset "CMI" "")
                 (asset "KEX" "")
                 (asset "WDC" "")
                 (asset "STTK" "")
                 (asset "DRD" "")
                 (asset "WHD" "")
                 (asset "KMT" "")
                 (asset "OR" "")
                 (asset "CBLL" "")
                 (asset "MU" "")
                 (asset "LION" "")
                 (asset "DAN" "")
                 (asset "EC" "")
                 (asset "EE" "")
                 (asset "ISSC" "")
                 (asset "BLTE" "")
                 (asset "SLB" "")
                 (asset "HII" "")
                 (asset "PANL" "")
                 (asset "PL" "")
                 (asset "TSEM" "")
                 (asset "TPB" "")
                 (asset "AMAL" "")
                 (asset "ATRO" "")
                 (asset "TENX" "")
                 (asset "GKOS" "")
                 (asset "MKSI" "")
                 (asset "UMC" "")
                 (asset "ONTO" "")
                 (asset "SLS" "")
                 (asset "NGL" "")
                 (asset "SPHR" "")
                 (asset "CX" "")
                 (asset "VRDN" "")
                 (asset "PPLT" "")
                 (asset "NESR" "")
                 (asset "EQX" "")
                 (asset "LAR" "")
                 (asset "MBX" "")
                 (asset "WT" "")
                 (asset "PACS" "")
                 (asset "PLTM" "")
                 (asset "ATI" "")
                 (asset "WNTR" "")
                 (asset "GGB" "")
                 (asset "AGI" "")
                 (asset "EPAM" "")
                 (asset "AMRX" "")
                 (asset "KALU" "")
                 (asset "MSGE" "")
                 (asset "TTI" "")
                 (asset "OUT" "")
                 (asset "EXK" "")
                 (asset "FLKR" "")
                 (asset "FSM" "")
                 (asset "TE" "")
                 (asset "EWY" "")
                 (asset "DG" "")
                 (asset "CMTL" "")
                 (asset "SD" "")
                 (asset "TER" "")
                 (asset "WBD" "")
                 (asset "TFPM" "")
                 (asset "VZLA" "")
                 (asset "GPCR" "")
                 (asset "AMTM" "")
                 (asset "NIKL" "")
                 (asset "SNDX" "")
                 (asset "AEM" "")
                 (asset "DC" "")
                 (asset "TWO" "")
                 (asset "GSL" "")
                 (asset "AMAT" "")
                 (asset "SNCY" "")
                 (asset "EFXT" "")
                 (asset "HTHT" "")
                 (asset "LRCX" "")
                 (asset "TCMD" "")
                 (asset "EGBN" "")
                 (asset "VSCO" "")
                 (asset "CNTX" "")
                 (asset "REMX" "")
                 (asset "CSTM" "")
                 (asset "FOLD" "")
                 (asset "VGZ" "")
                 (asset "DHC" "")
                 (asset "BTE" "")
                 (asset "CTGO" "")
                 (asset "TROO" "")
                 (asset "AA" "")
                 (asset "INDV" "")
                 (asset "CLYM" "")
                 (asset "CHRW" "")
                 (asset "ASML" "")
                 (asset "CELC" "")
                 (asset "TALK" "")
                 (asset "XME" "")
                 (asset "KLIC" "")
                 (asset "ABEV" "")
                 (asset "FORM" "")
                 (asset "MSBI" "")
                 (asset "RVMD" "")
                 (asset "HMY" "")
                 (asset "SGML" "")
                 (asset "ZIM" "")
                 (asset "NFGC" "")
                 (asset "GH" "")
                 (asset "SKM" "")
                 (asset "SA" "")
                 (asset "TRDA" "")
                 (asset "CMP" "")
                 (asset "CMPX" "")
                 (asset "GFI" "")
                 (asset "FTAI" "")
                 (asset "ITRG" "")
                 (asset "TDAY" "")
                 (asset "KEYS" "")
                 (asset "BSBR" "")
                 (asset "MTSI" "")
                 (asset "TECK" "")
                 (asset "ELVA" "")
                 (asset "VTYX" "")
                 (asset "ILMN" "")
                 (asset "ANNX" "")
                 (asset "LUV" "")
                 (asset "NRIX" "")
                 (asset "PEN" "")
                 (asset "MIRM" "")
                 (asset "CAH" "")
                 (asset "NEOG" "")
                 (asset "HAL" "")
                 (asset "NOV" "")
                 (asset "COCO" "")
                 (asset "PBR" "")
                 (asset "ECVT" "")
                 (asset "BORR" "")
                 (asset "TROX" "")
                 (asset "REGN" "")
                 (asset "MRTN" "")
                 (asset "MRNA" "")
                 (asset "RERE" "")
                 (asset "AKAM" "")
                 (asset "CTRI" "")
                 (asset "NG" "")
                 (asset "DY" "")
                 (asset "HP" "")
                 (asset "ARWR" "")
                 (asset "WFRD" "")
                 (asset "PATK" "")
                 (asset "GT" "")
                 (asset "CENX" "")
                 (asset "EXAS" "")
                 (asset "BFLY" "")
                 (asset "LLY" "")
                 (asset "ALM" "")
                 (asset "YETI" "")
                 (asset "DAR" "")
                 (asset "SPPP" "")
                 (asset "GLDG" "")
                 (asset "CMBT" "")
                 (asset "FWRD" "")
                 (asset "GLDD" "")
                 (asset "ODFL" "")
                 (asset "VTRS" "")
                 (asset "RES" "")
                 (asset "MAZE" "")
                 (asset "DLX" "")
                 (asset "FOSL" "")
                 (asset "DOCN" "")
                 (asset "UNF" "")
                 (asset "OSS" "")
                 (asset "SHMD" "")
                 (asset "COHR" "")
                 (asset "LITE" "")
                 (asset "GFS" "")
                 (asset "STX" "")
                 (asset "ASTI" "")
                 (asset "NXE" "")
                 (asset "OII" "")
                 (asset "ENVA" "")
                 (asset "GUTS" "")
                 (asset "ABX" "")
                 (asset "KEP" "")
                 (asset "VIAV" "")
                 (asset "GM" "")
                 (asset "CTMX" "")
                 (asset "WLDN" "")
                 (asset "KLAC" "")
                 (asset "ACA" "")
                 (asset "DNTH" "")
                 (asset "MUX" "")
                 (asset "EMBJ" "")
                 (asset "RUSHA" "")
                 (asset "IBRX" "")
                 (asset "CERS" "")
                 (asset "VOXR" "")
                 (asset "TXG" "")
                 (asset "JOE" "")
                 (asset "CALY" "")
                 (asset "HRMY" "")
                 (asset "AEO" "")
                 (asset "SOLS" "")
                 (asset "NTRA" "")
                 (asset "THM" "")
                 (asset "AIR" "")
                 (asset "FIGS" "")
                 (asset "RLMD" "")
                 (asset "SKYT" "")
                 (asset "CECO" "")
                 (asset "ALGN" "")
                 (asset "HCC" "")
                 (asset "JBIO" "")
                 (asset "BKV" "")
                 (asset "INDO" "")])])])])]
        [(group
          "Copy of Beam Chain Filter Top 3 instead of Top 8"
          [(weight-equal
            [(filter
              (stdev-return {:window 10})
              (select-top 3)
              [(group
                "Beam Filter: CORP, BTAL 28/6"
                [(weight-equal
                  [(if
                    (> (cumulative-return "HYG" {:window 15}) 0)
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "HYG" {:window 90})
                         (cumulative-return "HYG" {:window 80}))
                        [(asset
                          "CORP"
                          "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "SHY" {:window 45})
                             (cumulative-return "SHY" {:window 50}))
                            [(weight-equal
                              [(if
                                (>
                                 (moving-average-return
                                  "IWM"
                                  {:window 100})
                                 (moving-average-return
                                  "LQD"
                                  {:window 100}))
                                [(asset
                                  "BTAL"
                                  "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "LQD"
                                      {:window 70})
                                     (cumulative-return
                                      "CORP"
                                      {:window 65}))
                                    [(weight-equal
                                      [(if
                                        (>
                                         (cumulative-return
                                          "LQD"
                                          {:window 80})
                                         (cumulative-return
                                          "CORP"
                                          {:window 80}))
                                        [(asset
                                          "CORP"
                                          "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                                        [(asset
                                          "BIL"
                                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "LQD" {:window 70})
                                 (cumulative-return
                                  "CORP"
                                  {:window 65}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "LQD"
                                      {:window 80})
                                     (cumulative-return
                                      "CORP"
                                      {:window 80}))
                                    [(asset
                                      "CORP"
                                      "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "SHY" {:window 45})
                         (cumulative-return "SHY" {:window 50}))
                        [(weight-equal
                          [(if
                            (>
                             (moving-average-return
                              "IWM"
                              {:window 100})
                             (moving-average-return
                              "LQD"
                              {:window 100}))
                            [(asset
                              "BTAL"
                              "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "LQD" {:window 70})
                                 (cumulative-return
                                  "CORP"
                                  {:window 65}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "LQD"
                                      {:window 80})
                                     (cumulative-return
                                      "CORP"
                                      {:window 80}))
                                    [(asset
                                      "CORP"
                                      "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "LQD" {:window 70})
                             (cumulative-return "CORP" {:window 65}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "LQD" {:window 80})
                                 (cumulative-return
                                  "CORP"
                                  {:window 80}))
                                [(asset
                                  "CORP"
                                  "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
               (group
                "Beam Filter: GLD, CORP 32/5.6"
                [(weight-equal
                  [(if
                    (>
                     (moving-average-return "QQQ" {:window 80})
                     (moving-average-return "IWM" {:window 40}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "GLD" {:window 50})
                         (cumulative-return "GLD" {:window 60}))
                        [(asset
                          "GLD"
                          "SPDR Gold Trust - SPDR Gold Shares ETF")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "LQD" {:window 45})
                             (cumulative-return "CORP" {:window 45}))
                            [(weight-equal
                              [(if
                                (> (rsi "CORP" {:window 5}) 40)
                                [(asset
                                  "CORP"
                                  "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "QQQ"
                                      {:window 90})
                                     (cumulative-return
                                      "QQQ"
                                      {:window 70}))
                                    [(weight-equal
                                      [(if
                                        (>
                                         (rsi "EWG" {:window 15})
                                         (rsi "EWU" {:window 20}))
                                        [(asset
                                          "GLD"
                                          "SPDR Gold Trust - SPDR Gold Shares ETF")]
                                        [(asset
                                          "BIL"
                                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "QQQ" {:window 90})
                                 (cumulative-return
                                  "QQQ"
                                  {:window 70}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (rsi "EWG" {:window 15})
                                     (rsi "EWU" {:window 20}))
                                    [(asset
                                      "GLD"
                                      "SPDR Gold Trust - SPDR Gold Shares ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "LQD" {:window 45})
                         (cumulative-return "CORP" {:window 45}))
                        [(weight-equal
                          [(if
                            (> (rsi "CORP" {:window 5}) 40)
                            [(asset
                              "CORP"
                              "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "QQQ" {:window 90})
                                 (cumulative-return
                                  "QQQ"
                                  {:window 70}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (rsi "EWG" {:window 15})
                                     (rsi "EWU" {:window 20}))
                                    [(asset
                                      "GLD"
                                      "SPDR Gold Trust - SPDR Gold Shares ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "QQQ" {:window 90})
                             (cumulative-return "QQQ" {:window 70}))
                            [(weight-equal
                              [(if
                                (>
                                 (rsi "EWG" {:window 15})
                                 (rsi "EWU" {:window 20}))
                                [(asset
                                  "GLD"
                                  "SPDR Gold Trust - SPDR Gold Shares ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
               (group
                "Beam Filter: GLD, QQQ 319/54"
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "QQQ" {:window 90})
                     (cumulative-return "XLK" {:window 70}))
                    [(weight-equal
                      [(if
                        (>
                         (moving-average-return "DIA" {:window 100})
                         (moving-average-return "SHY" {:window 80}))
                        [(asset
                          "GDXU"
                          "Bank of Montreal - MicroSectors Gold Miners 3X Leveraged ETN")]
                        [(weight-equal
                          [(group
                            "TQQQ 1"
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "XLK" {:window 30})
                                 (cumulative-return "DIA" {:window 5}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (rsi "XLK" {:window 25})
                                     (rsi "DIA" {:window 30}))
                                    [(asset
                                      "TQQQ"
                                      "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                    [(weight-equal
                                      [(group
                                        "TQQQ 2"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (cumulative-return
                                              "SMH"
                                              {:window 80})
                                             (cumulative-return
                                              "SMH"
                                              {:window 65}))
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (cumulative-return
                                                  "DIA"
                                                  {:window 80})
                                                 (cumulative-return
                                                  "DIA"
                                                  {:window 65}))
                                                [(asset
                                                  "TQQQ"
                                                  "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                [(asset
                                                  "BIL"
                                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                            [(asset
                                              "BIL"
                                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                                [(group
                                  "TQQQ 2"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (cumulative-return
                                        "SMH"
                                        {:window 80})
                                       (cumulative-return
                                        "SMH"
                                        {:window 65}))
                                      [(weight-equal
                                        [(if
                                          (>
                                           (cumulative-return
                                            "DIA"
                                            {:window 80})
                                           (cumulative-return
                                            "DIA"
                                            {:window 65}))
                                          [(asset
                                            "TQQQ"
                                            "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                          [(asset
                                            "BIL"
                                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                      [(asset
                                        "BIL"
                                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                    [(group
                      "TQQQ 1"
                      [(weight-equal
                        [(if
                          (>
                           (cumulative-return "XLK" {:window 30})
                           (cumulative-return "DIA" {:window 5}))
                          [(weight-equal
                            [(if
                              (>
                               (rsi "XLK" {:window 25})
                               (rsi "DIA" {:window 30}))
                              [(asset
                                "TQQQ"
                                "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                              [(weight-equal
                                [(group
                                  "TQQQ 2"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (cumulative-return
                                        "SMH"
                                        {:window 80})
                                       (cumulative-return
                                        "SMH"
                                        {:window 65}))
                                      [(weight-equal
                                        [(if
                                          (>
                                           (cumulative-return
                                            "DIA"
                                            {:window 80})
                                           (cumulative-return
                                            "DIA"
                                            {:window 65}))
                                          [(asset
                                            "TQQQ"
                                            "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                          [(asset
                                            "BIL"
                                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                      [(asset
                                        "BIL"
                                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                          [(group
                            "TQQQ 2"
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "SMH" {:window 80})
                                 (cumulative-return
                                  "SMH"
                                  {:window 65}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "DIA"
                                      {:window 80})
                                     (cumulative-return
                                      "DIA"
                                      {:window 65}))
                                    [(asset
                                      "TQQQ"
                                      "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])
               (group
                "Beam Filter: AIQ, ICLN, CIBR 64/9"
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "XLF" {:window 25})
                     (cumulative-return "CIBR" {:window 70}))
                    [(weight-equal
                      [(if
                        (> (cumulative-return "AIQ" {:window 55}) 0)
                        [(asset
                          "CIBR"
                          "First Trust Exchange-Traded Fund III - First Trust NASDAQ Cybersecurity ETF")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "XLF" {:window 20})
                             (cumulative-return "DIA" {:window 85}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "XLI" {:window 25})
                                 (cumulative-return
                                  "DIA"
                                  {:window 65}))
                                [(asset
                                  "ICLN"
                                  "BlackRock Institutional Trust Company N.A. - iShares Global Clean Energy ETF")]
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "XLK"
                                      {:window 25})
                                     (cumulative-return
                                      "XLI"
                                      {:window 5}))
                                    [(weight-equal
                                      [(if
                                        (>
                                         (stdev-return
                                          "XLK"
                                          {:window 10})
                                         (stdev-return
                                          "XLK"
                                          {:window 20}))
                                        [(asset
                                          "AIQ"
                                          "Global X Funds - Global X Artificial Intelligence & Technology ETF")]
                                        [(asset
                                          "BIL"
                                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "XLK" {:window 25})
                                 (cumulative-return "XLI" {:window 5}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (stdev-return "XLK" {:window 10})
                                     (stdev-return "XLK" {:window 20}))
                                    [(asset
                                      "AIQ"
                                      "Global X Funds - Global X Artificial Intelligence & Technology ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "XLF" {:window 20})
                         (cumulative-return "DIA" {:window 85}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "XLI" {:window 25})
                             (cumulative-return "DIA" {:window 65}))
                            [(asset
                              "ICLN"
                              "BlackRock Institutional Trust Company N.A. - iShares Global Clean Energy ETF")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "XLK" {:window 25})
                                 (cumulative-return "XLI" {:window 5}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (stdev-return "XLK" {:window 10})
                                     (stdev-return "XLK" {:window 20}))
                                    [(asset
                                      "AIQ"
                                      "Global X Funds - Global X Artificial Intelligence & Technology ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "XLK" {:window 25})
                             (cumulative-return "XLI" {:window 5}))
                            [(weight-equal
                              [(if
                                (>
                                 (stdev-return "XLK" {:window 10})
                                 (stdev-return "XLK" {:window 20}))
                                [(asset
                                  "AIQ"
                                  "Global X Funds - Global X Artificial Intelligence & Technology ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
               (group
                "Beam FIlter: SOXX, KMLM, HYG 156/21"
                [(weight-equal
                  [(if
                    (>
                     (moving-average-return "HYG" {:window 90})
                     (moving-average-return "XLF" {:window 60}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "LQD" {:window 90})
                         (cumulative-return "EFA" {:window 75}))
                        [(asset
                          "SOXL"
                          "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                        [(weight-equal
                          [(if
                            (>
                             (stdev-return "LQD" {:window 20})
                             (stdev-return "HYG" {:window 30}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "HYG" {:window 90})
                                 (cumulative-return
                                  "QQQ"
                                  {:window 15}))
                                [(asset
                                  "HYG"
                                  "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "QQQ"
                                      {:window 15})
                                     (cumulative-return
                                      "LQD"
                                      {:window 30}))
                                    [(weight-equal
                                      [(if
                                        (>
                                         (rsi "IWM" {:window 5})
                                         (rsi "DIA" {:window 10}))
                                        [(asset
                                          "KMLM"
                                          "KraneShares Trust - KraneShares Mount Lucas Managed Futures Index Strategy ETF")]
                                        [(asset
                                          "BIL"
                                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "QQQ" {:window 15})
                                 (cumulative-return
                                  "LQD"
                                  {:window 30}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (rsi "IWM" {:window 5})
                                     (rsi "DIA" {:window 10}))
                                    [(asset
                                      "KMLM"
                                      "KraneShares Trust - KraneShares Mount Lucas Managed Futures Index Strategy ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (stdev-return "LQD" {:window 20})
                         (stdev-return "HYG" {:window 30}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "HYG" {:window 90})
                             (cumulative-return "QQQ" {:window 15}))
                            [(asset
                              "HYG"
                              "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "QQQ" {:window 15})
                                 (cumulative-return
                                  "LQD"
                                  {:window 30}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (rsi "IWM" {:window 5})
                                     (rsi "DIA" {:window 10}))
                                    [(asset
                                      "KMLM"
                                      "KraneShares Trust - KraneShares Mount Lucas Managed Futures Index Strategy ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "QQQ" {:window 15})
                             (cumulative-return "LQD" {:window 30}))
                            [(weight-equal
                              [(if
                                (>
                                 (rsi "IWM" {:window 5})
                                 (rsi "DIA" {:window 10}))
                                [(asset
                                  "KMLM"
                                  "KraneShares Trust - KraneShares Mount Lucas Managed Futures Index Strategy ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
               (group
                "Beam Filter: TMV, GLD 103/10"
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "EWU" {:window 5})
                     (cumulative-return "IEF" {:window 5}))
                    [(weight-equal
                      [(if
                        (>
                         (stdev-return "HYG" {:window 10})
                         (moving-average-return "EWU" {:window 20}))
                        [(asset
                          "GLD"
                          "SPDR Gold Trust - SPDR Gold Shares ETF")]
                        [(weight-equal
                          [(if
                            (>
                             (rsi "TLT" {:window 20})
                             (rsi "HYG" {:window 20}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "IEF" {:window 75})
                                 (cumulative-return
                                  "EWU"
                                  {:window 80}))
                                [(asset
                                  "TMV"
                                  "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "TLT"
                                      {:window 80})
                                     (cumulative-return
                                      "HYG"
                                      {:window 10}))
                                    [(weight-equal
                                      [(if
                                        (>
                                         (cumulative-return
                                          "GLD"
                                          {:window 60})
                                         8)
                                        [(asset
                                          "TMV"
                                          "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                                        [(asset
                                          "BIL"
                                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "TLT" {:window 80})
                                 (cumulative-return
                                  "HYG"
                                  {:window 10}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "GLD"
                                      {:window 60})
                                     8)
                                    [(asset
                                      "TMV"
                                      "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (rsi "TLT" {:window 20})
                         (rsi "HYG" {:window 20}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "IEF" {:window 75})
                             (cumulative-return "EWU" {:window 80}))
                            [(asset
                              "TMV"
                              "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "TLT" {:window 80})
                                 (cumulative-return
                                  "HYG"
                                  {:window 10}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "GLD"
                                      {:window 60})
                                     8)
                                    [(asset
                                      "TMV"
                                      "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "TLT" {:window 80})
                             (cumulative-return "HYG" {:window 10}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "GLD" {:window 60})
                                 8)
                                [(asset
                                  "TMV"
                                  "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
               (group
                "Beam Filter: GLD, SOXX, BTAL 124/17.5"
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "IWM" {:window 80})
                     (cumulative-return "EWG" {:window 75}))
                    [(weight-equal
                      [(if
                        (>
                         (moving-average-return "QQQ" {:window 60})
                         (moving-average-return "IWM" {:window 100}))
                        [(asset
                          "BTAL"
                          "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "DIA" {:window 55})
                             (cumulative-return "IWM" {:window 40}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "EFA" {:window 20})
                                 -8)
                                [(asset
                                  "UGL"
                                  "ProShares Trust - ProShares Ultra Gold 2x Shares")]
                                [(weight-equal
                                  [(if
                                    (>
                                     (stdev-return "EFA" {:window 50})
                                     (stdev-return "EFA" {:window 30}))
                                    [(weight-equal
                                      [(if
                                        (>
                                         (cumulative-return
                                          "IWM"
                                          {:window 70})
                                         (cumulative-return
                                          "SOXX"
                                          {:window 50}))
                                        [(asset
                                          "SOXL"
                                          "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                                        [(weight-equal
                                          [(asset
                                            "BIL"
                                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                            [(weight-equal
                              [(if
                                (>
                                 (stdev-return "EFA" {:window 50})
                                 (stdev-return "EFA" {:window 30}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "IWM"
                                      {:window 70})
                                     (cumulative-return
                                      "SOXX"
                                      {:window 50}))
                                    [(asset
                                      "SOXL"
                                      "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                                    [(weight-equal
                                      [(asset
                                        "BIL"
                                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "DIA" {:window 55})
                         (cumulative-return "IWM" {:window 40}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "EFA" {:window 20})
                             -8)
                            [(asset
                              "UGL"
                              "ProShares Trust - ProShares Ultra Gold 2x Shares")]
                            [(weight-equal
                              [(if
                                (>
                                 (stdev-return "EFA" {:window 50})
                                 (stdev-return "EFA" {:window 30}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "IWM"
                                      {:window 70})
                                     (cumulative-return
                                      "SOXX"
                                      {:window 50}))
                                    [(asset
                                      "SOXL"
                                      "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                                    [(weight-equal
                                      [(asset
                                        "BIL"
                                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (stdev-return "EFA" {:window 50})
                             (stdev-return "EFA" {:window 30}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "IWM" {:window 70})
                                 (cumulative-return
                                  "SOXX"
                                  {:window 50}))
                                [(asset
                                  "SOXL"
                                  "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                                [(weight-equal
                                  [(asset
                                    "BIL"
                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
               (group
                "Beam Filter: HYG, BTAL 28/9.5"
                [(weight-equal
                  [(if
                    (>
                     (stdev-return "IWM" {:window 30})
                     (stdev-return "QQQ" {:window 40}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "HYG" {:window 75})
                         (cumulative-return "QQQ" {:window 5}))
                        [(asset
                          "HYG"
                          "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "QQQ" {:window 5})
                             (cumulative-return "HYG" {:window 55}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "IWM" {:window 85})
                                 (cumulative-return
                                  "BTAL"
                                  {:window 65}))
                                [(asset
                                  "BTAL"
                                  "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "BTAL"
                                      {:window 60})
                                     (cumulative-return
                                      "BTAL"
                                      {:window 55}))
                                    [(weight-equal
                                      [(if
                                        (>
                                         (cumulative-return
                                          "BTAL"
                                          {:window 90})
                                         (cumulative-return
                                          "IWM"
                                          {:window 10}))
                                        [(asset
                                          "HYG"
                                          "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                                        [(weight-equal
                                          [(asset
                                            "BIL"
                                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return
                                  "BTAL"
                                  {:window 60})
                                 (cumulative-return
                                  "BTAL"
                                  {:window 55}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "BTAL"
                                      {:window 90})
                                     (cumulative-return
                                      "IWM"
                                      {:window 10}))
                                    [(asset
                                      "HYG"
                                      "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                                    [(weight-equal
                                      [(asset
                                        "BIL"
                                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "QQQ" {:window 5})
                         (cumulative-return "HYG" {:window 55}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "IWM" {:window 85})
                             (cumulative-return "BTAL" {:window 65}))
                            [(asset
                              "BTAL"
                              "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return
                                  "BTAL"
                                  {:window 60})
                                 (cumulative-return
                                  "BTAL"
                                  {:window 55}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "BTAL"
                                      {:window 90})
                                     (cumulative-return
                                      "IWM"
                                      {:window 10}))
                                    [(asset
                                      "HYG"
                                      "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                                    [(weight-equal
                                      [(asset
                                        "BIL"
                                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "BTAL" {:window 60})
                             (cumulative-return "BTAL" {:window 55}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return
                                  "BTAL"
                                  {:window 90})
                                 (cumulative-return
                                  "IWM"
                                  {:window 10}))
                                [(asset
                                  "HYG"
                                  "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                                [(weight-equal
                                  [(asset
                                    "BIL"
                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
               (group
                "Beam Filter: BITO, IEF 85/23"
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "EWG" {:window 45})
                     (cumulative-return "XLI" {:window 75}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "EFA" {:window 55})
                         (cumulative-return "TLT" {:window 75}))
                        [(asset
                          "IEF"
                          "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "XLY" {:window 45})
                             (cumulative-return "IWM" {:window 35}))
                            [(weight-equal
                              [(if
                                (>
                                 (stdev-return "XLF" {:window 10})
                                 (stdev-return "XLF" {:window 40}))
                                [(asset
                                  "BITO"
                                  "ProShares Trust - ProShares Bitcoin ETF")]
                                [(weight-equal
                                  [(if
                                    (>
                                     (moving-average-return
                                      "HYG"
                                      {:window 90})
                                     (moving-average-return
                                      "SHY"
                                      {:window 90}))
                                    [(weight-equal
                                      [(if
                                        (>
                                         (stdev-return
                                          "IWM"
                                          {:window 30})
                                         (stdev-return
                                          "IWM"
                                          {:window 40}))
                                        [(asset
                                          "IEF"
                                          "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                                        [(asset
                                          "BIL"
                                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                            [(weight-equal
                              [(if
                                (>
                                 (moving-average-return
                                  "HYG"
                                  {:window 90})
                                 (moving-average-return
                                  "SHY"
                                  {:window 90}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (stdev-return "IWM" {:window 30})
                                     (stdev-return "IWM" {:window 40}))
                                    [(asset
                                      "IEF"
                                      "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "XLY" {:window 45})
                         (cumulative-return "IWM" {:window 35}))
                        [(weight-equal
                          [(if
                            (>
                             (stdev-return "XLF" {:window 10})
                             (stdev-return "XLF" {:window 40}))
                            [(asset
                              "BITO"
                              "ProShares Trust - ProShares Bitcoin ETF")]
                            [(weight-equal
                              [(if
                                (>
                                 (moving-average-return
                                  "HYG"
                                  {:window 90})
                                 (moving-average-return
                                  "SHY"
                                  {:window 90}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (stdev-return "IWM" {:window 30})
                                     (stdev-return "IWM" {:window 40}))
                                    [(asset
                                      "IEF"
                                      "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (moving-average-return "HYG" {:window 90})
                             (moving-average-return
                              "SHY"
                              {:window 90}))
                            [(weight-equal
                              [(if
                                (>
                                 (stdev-return "IWM" {:window 30})
                                 (stdev-return "IWM" {:window 40}))
                                [(asset
                                  "IEF"
                                  "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
               (group
                "Beam Filter: XLK, XLP, XLE 75/4.3"
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "IWM" {:window 5})
                     (cumulative-return "USO" {:window 5}))
                    [(weight-equal
                      [(if
                        (>
                         (moving-average-return "XLI" {:window 20})
                         (moving-average-return "IWM" {:window 40}))
                        [(asset
                          "XLP"
                          "SSgA Active Trust - Consumer Staples Select Sector SPDR")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "SOXX" {:window 65})
                             (cumulative-return "IWM" {:window 30}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "IWM" {:window 5})
                                 (cumulative-return
                                  "XLE"
                                  {:window 10}))
                                [(asset
                                  "XLE"
                                  "SSgA Active Trust - The Energy Select Sector SPDR Fund")]
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "XLI"
                                      {:window 80})
                                     (cumulative-return
                                      "XLE"
                                      {:window 30}))
                                    [(weight-equal
                                      [(if
                                        (>
                                         (cumulative-return
                                          "DIA"
                                          {:window 30})
                                         (cumulative-return
                                          "USO"
                                          {:window 60}))
                                        [(asset
                                          "XLK"
                                          "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                                        [(asset
                                          "BIL"
                                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "XLI" {:window 80})
                                 (cumulative-return
                                  "XLE"
                                  {:window 30}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "DIA"
                                      {:window 30})
                                     (cumulative-return
                                      "USO"
                                      {:window 60}))
                                    [(asset
                                      "XLK"
                                      "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "SOXX" {:window 65})
                         (cumulative-return "IWM" {:window 30}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "IWM" {:window 5})
                             (cumulative-return "XLE" {:window 10}))
                            [(asset
                              "XLE"
                              "SSgA Active Trust - The Energy Select Sector SPDR Fund")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "XLI" {:window 80})
                                 (cumulative-return
                                  "XLE"
                                  {:window 30}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "DIA"
                                      {:window 30})
                                     (cumulative-return
                                      "USO"
                                      {:window 60}))
                                    [(asset
                                      "XLK"
                                      "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "XLI" {:window 80})
                             (cumulative-return "XLE" {:window 30}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "DIA" {:window 30})
                                 (cumulative-return
                                  "USO"
                                  {:window 60}))
                                [(asset
                                  "XLK"
                                  "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])]
    [(group
      "Copy of Beam Chain Filter Top 3 instead of Top 8"
      [(weight-equal
        [(filter
          (stdev-return {:window 10})
          (select-top 3)
          [(group
            "Beam Filter: CORP, BTAL 28/6"
            [(weight-equal
              [(if
                (> (cumulative-return "HYG" {:window 15}) 0)
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "HYG" {:window 90})
                     (cumulative-return "HYG" {:window 80}))
                    [(asset
                      "CORP"
                      "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "SHY" {:window 45})
                         (cumulative-return "SHY" {:window 50}))
                        [(weight-equal
                          [(if
                            (>
                             (moving-average-return
                              "IWM"
                              {:window 100})
                             (moving-average-return
                              "LQD"
                              {:window 100}))
                            [(asset
                              "BTAL"
                              "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "LQD" {:window 70})
                                 (cumulative-return
                                  "CORP"
                                  {:window 65}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "LQD"
                                      {:window 80})
                                     (cumulative-return
                                      "CORP"
                                      {:window 80}))
                                    [(asset
                                      "CORP"
                                      "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "LQD" {:window 70})
                             (cumulative-return "CORP" {:window 65}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "LQD" {:window 80})
                                 (cumulative-return
                                  "CORP"
                                  {:window 80}))
                                [(asset
                                  "CORP"
                                  "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "SHY" {:window 45})
                     (cumulative-return "SHY" {:window 50}))
                    [(weight-equal
                      [(if
                        (>
                         (moving-average-return "IWM" {:window 100})
                         (moving-average-return "LQD" {:window 100}))
                        [(asset
                          "BTAL"
                          "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "LQD" {:window 70})
                             (cumulative-return "CORP" {:window 65}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "LQD" {:window 80})
                                 (cumulative-return
                                  "CORP"
                                  {:window 80}))
                                [(asset
                                  "CORP"
                                  "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "LQD" {:window 70})
                         (cumulative-return "CORP" {:window 65}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "LQD" {:window 80})
                             (cumulative-return "CORP" {:window 80}))
                            [(asset
                              "CORP"
                              "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
           (group
            "Beam Filter: GLD, CORP 32/5.6"
            [(weight-equal
              [(if
                (>
                 (moving-average-return "QQQ" {:window 80})
                 (moving-average-return "IWM" {:window 40}))
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "GLD" {:window 50})
                     (cumulative-return "GLD" {:window 60}))
                    [(asset
                      "GLD"
                      "SPDR Gold Trust - SPDR Gold Shares ETF")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "LQD" {:window 45})
                         (cumulative-return "CORP" {:window 45}))
                        [(weight-equal
                          [(if
                            (> (rsi "CORP" {:window 5}) 40)
                            [(asset
                              "CORP"
                              "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "QQQ" {:window 90})
                                 (cumulative-return
                                  "QQQ"
                                  {:window 70}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (rsi "EWG" {:window 15})
                                     (rsi "EWU" {:window 20}))
                                    [(asset
                                      "GLD"
                                      "SPDR Gold Trust - SPDR Gold Shares ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "QQQ" {:window 90})
                             (cumulative-return "QQQ" {:window 70}))
                            [(weight-equal
                              [(if
                                (>
                                 (rsi "EWG" {:window 15})
                                 (rsi "EWU" {:window 20}))
                                [(asset
                                  "GLD"
                                  "SPDR Gold Trust - SPDR Gold Shares ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "LQD" {:window 45})
                     (cumulative-return "CORP" {:window 45}))
                    [(weight-equal
                      [(if
                        (> (rsi "CORP" {:window 5}) 40)
                        [(asset
                          "CORP"
                          "Pimco Exchange Traded Fund - PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "QQQ" {:window 90})
                             (cumulative-return "QQQ" {:window 70}))
                            [(weight-equal
                              [(if
                                (>
                                 (rsi "EWG" {:window 15})
                                 (rsi "EWU" {:window 20}))
                                [(asset
                                  "GLD"
                                  "SPDR Gold Trust - SPDR Gold Shares ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "QQQ" {:window 90})
                         (cumulative-return "QQQ" {:window 70}))
                        [(weight-equal
                          [(if
                            (>
                             (rsi "EWG" {:window 15})
                             (rsi "EWU" {:window 20}))
                            [(asset
                              "GLD"
                              "SPDR Gold Trust - SPDR Gold Shares ETF")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
           (group
            "Beam Filter: GLD, QQQ 319/54"
            [(weight-equal
              [(if
                (>
                 (cumulative-return "QQQ" {:window 90})
                 (cumulative-return "XLK" {:window 70}))
                [(weight-equal
                  [(if
                    (>
                     (moving-average-return "DIA" {:window 100})
                     (moving-average-return "SHY" {:window 80}))
                    [(asset
                      "GDXU"
                      "Bank of Montreal - MicroSectors Gold Miners 3X Leveraged ETN")]
                    [(weight-equal
                      [(group
                        "TQQQ 1"
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "XLK" {:window 30})
                             (cumulative-return "DIA" {:window 5}))
                            [(weight-equal
                              [(if
                                (>
                                 (rsi "XLK" {:window 25})
                                 (rsi "DIA" {:window 30}))
                                [(asset
                                  "TQQQ"
                                  "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                [(weight-equal
                                  [(group
                                    "TQQQ 2"
                                    [(weight-equal
                                      [(if
                                        (>
                                         (cumulative-return
                                          "SMH"
                                          {:window 80})
                                         (cumulative-return
                                          "SMH"
                                          {:window 65}))
                                        [(weight-equal
                                          [(if
                                            (>
                                             (cumulative-return
                                              "DIA"
                                              {:window 80})
                                             (cumulative-return
                                              "DIA"
                                              {:window 65}))
                                            [(asset
                                              "TQQQ"
                                              "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                            [(asset
                                              "BIL"
                                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                        [(asset
                                          "BIL"
                                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                            [(group
                              "TQQQ 2"
                              [(weight-equal
                                [(if
                                  (>
                                   (cumulative-return
                                    "SMH"
                                    {:window 80})
                                   (cumulative-return
                                    "SMH"
                                    {:window 65}))
                                  [(weight-equal
                                    [(if
                                      (>
                                       (cumulative-return
                                        "DIA"
                                        {:window 80})
                                       (cumulative-return
                                        "DIA"
                                        {:window 65}))
                                      [(asset
                                        "TQQQ"
                                        "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                      [(asset
                                        "BIL"
                                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                  [(asset
                                    "BIL"
                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                [(group
                  "TQQQ 1"
                  [(weight-equal
                    [(if
                      (>
                       (cumulative-return "XLK" {:window 30})
                       (cumulative-return "DIA" {:window 5}))
                      [(weight-equal
                        [(if
                          (>
                           (rsi "XLK" {:window 25})
                           (rsi "DIA" {:window 30}))
                          [(asset
                            "TQQQ"
                            "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                          [(weight-equal
                            [(group
                              "TQQQ 2"
                              [(weight-equal
                                [(if
                                  (>
                                   (cumulative-return
                                    "SMH"
                                    {:window 80})
                                   (cumulative-return
                                    "SMH"
                                    {:window 65}))
                                  [(weight-equal
                                    [(if
                                      (>
                                       (cumulative-return
                                        "DIA"
                                        {:window 80})
                                       (cumulative-return
                                        "DIA"
                                        {:window 65}))
                                      [(asset
                                        "TQQQ"
                                        "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                      [(asset
                                        "BIL"
                                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                  [(asset
                                    "BIL"
                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                      [(group
                        "TQQQ 2"
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "SMH" {:window 80})
                             (cumulative-return "SMH" {:window 65}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "DIA" {:window 80})
                                 (cumulative-return
                                  "DIA"
                                  {:window 65}))
                                [(asset
                                  "TQQQ"
                                  "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])
           (group
            "Beam Filter: AIQ, ICLN, CIBR 64/9"
            [(weight-equal
              [(if
                (>
                 (cumulative-return "XLF" {:window 25})
                 (cumulative-return "CIBR" {:window 70}))
                [(weight-equal
                  [(if
                    (> (cumulative-return "AIQ" {:window 55}) 0)
                    [(asset
                      "CIBR"
                      "First Trust Exchange-Traded Fund III - First Trust NASDAQ Cybersecurity ETF")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "XLF" {:window 20})
                         (cumulative-return "DIA" {:window 85}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "XLI" {:window 25})
                             (cumulative-return "DIA" {:window 65}))
                            [(asset
                              "ICLN"
                              "BlackRock Institutional Trust Company N.A. - iShares Global Clean Energy ETF")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "XLK" {:window 25})
                                 (cumulative-return "XLI" {:window 5}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (stdev-return "XLK" {:window 10})
                                     (stdev-return "XLK" {:window 20}))
                                    [(asset
                                      "AIQ"
                                      "Global X Funds - Global X Artificial Intelligence & Technology ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "XLK" {:window 25})
                             (cumulative-return "XLI" {:window 5}))
                            [(weight-equal
                              [(if
                                (>
                                 (stdev-return "XLK" {:window 10})
                                 (stdev-return "XLK" {:window 20}))
                                [(asset
                                  "AIQ"
                                  "Global X Funds - Global X Artificial Intelligence & Technology ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "XLF" {:window 20})
                     (cumulative-return "DIA" {:window 85}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "XLI" {:window 25})
                         (cumulative-return "DIA" {:window 65}))
                        [(asset
                          "ICLN"
                          "BlackRock Institutional Trust Company N.A. - iShares Global Clean Energy ETF")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "XLK" {:window 25})
                             (cumulative-return "XLI" {:window 5}))
                            [(weight-equal
                              [(if
                                (>
                                 (stdev-return "XLK" {:window 10})
                                 (stdev-return "XLK" {:window 20}))
                                [(asset
                                  "AIQ"
                                  "Global X Funds - Global X Artificial Intelligence & Technology ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "XLK" {:window 25})
                         (cumulative-return "XLI" {:window 5}))
                        [(weight-equal
                          [(if
                            (>
                             (stdev-return "XLK" {:window 10})
                             (stdev-return "XLK" {:window 20}))
                            [(asset
                              "AIQ"
                              "Global X Funds - Global X Artificial Intelligence & Technology ETF")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
           (group
            "Beam FIlter: SOXX, KMLM, HYG 156/21"
            [(weight-equal
              [(if
                (>
                 (moving-average-return "HYG" {:window 90})
                 (moving-average-return "XLF" {:window 60}))
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "LQD" {:window 90})
                     (cumulative-return "EFA" {:window 75}))
                    [(asset
                      "SOXL"
                      "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                    [(weight-equal
                      [(if
                        (>
                         (stdev-return "LQD" {:window 20})
                         (stdev-return "HYG" {:window 30}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "HYG" {:window 90})
                             (cumulative-return "QQQ" {:window 15}))
                            [(asset
                              "HYG"
                              "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "QQQ" {:window 15})
                                 (cumulative-return
                                  "LQD"
                                  {:window 30}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (rsi "IWM" {:window 5})
                                     (rsi "DIA" {:window 10}))
                                    [(asset
                                      "KMLM"
                                      "KraneShares Trust - KraneShares Mount Lucas Managed Futures Index Strategy ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "QQQ" {:window 15})
                             (cumulative-return "LQD" {:window 30}))
                            [(weight-equal
                              [(if
                                (>
                                 (rsi "IWM" {:window 5})
                                 (rsi "DIA" {:window 10}))
                                [(asset
                                  "KMLM"
                                  "KraneShares Trust - KraneShares Mount Lucas Managed Futures Index Strategy ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                [(weight-equal
                  [(if
                    (>
                     (stdev-return "LQD" {:window 20})
                     (stdev-return "HYG" {:window 30}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "HYG" {:window 90})
                         (cumulative-return "QQQ" {:window 15}))
                        [(asset
                          "HYG"
                          "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "QQQ" {:window 15})
                             (cumulative-return "LQD" {:window 30}))
                            [(weight-equal
                              [(if
                                (>
                                 (rsi "IWM" {:window 5})
                                 (rsi "DIA" {:window 10}))
                                [(asset
                                  "KMLM"
                                  "KraneShares Trust - KraneShares Mount Lucas Managed Futures Index Strategy ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "QQQ" {:window 15})
                         (cumulative-return "LQD" {:window 30}))
                        [(weight-equal
                          [(if
                            (>
                             (rsi "IWM" {:window 5})
                             (rsi "DIA" {:window 10}))
                            [(asset
                              "KMLM"
                              "KraneShares Trust - KraneShares Mount Lucas Managed Futures Index Strategy ETF")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
           (group
            "Beam Filter: TMV, GLD 103/10"
            [(weight-equal
              [(if
                (>
                 (cumulative-return "EWU" {:window 5})
                 (cumulative-return "IEF" {:window 5}))
                [(weight-equal
                  [(if
                    (>
                     (stdev-return "HYG" {:window 10})
                     (moving-average-return "EWU" {:window 20}))
                    [(asset
                      "GLD"
                      "SPDR Gold Trust - SPDR Gold Shares ETF")]
                    [(weight-equal
                      [(if
                        (>
                         (rsi "TLT" {:window 20})
                         (rsi "HYG" {:window 20}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "IEF" {:window 75})
                             (cumulative-return "EWU" {:window 80}))
                            [(asset
                              "TMV"
                              "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "TLT" {:window 80})
                                 (cumulative-return
                                  "HYG"
                                  {:window 10}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "GLD"
                                      {:window 60})
                                     8)
                                    [(asset
                                      "TMV"
                                      "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "TLT" {:window 80})
                             (cumulative-return "HYG" {:window 10}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "GLD" {:window 60})
                                 8)
                                [(asset
                                  "TMV"
                                  "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                [(weight-equal
                  [(if
                    (>
                     (rsi "TLT" {:window 20})
                     (rsi "HYG" {:window 20}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "IEF" {:window 75})
                         (cumulative-return "EWU" {:window 80}))
                        [(asset
                          "TMV"
                          "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "TLT" {:window 80})
                             (cumulative-return "HYG" {:window 10}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "GLD" {:window 60})
                                 8)
                                [(asset
                                  "TMV"
                                  "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "TLT" {:window 80})
                         (cumulative-return "HYG" {:window 10}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "GLD" {:window 60})
                             8)
                            [(asset
                              "TMV"
                              "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
           (group
            "Beam Filter: GLD, SOXX, BTAL 124/17.5"
            [(weight-equal
              [(if
                (>
                 (cumulative-return "IWM" {:window 80})
                 (cumulative-return "EWG" {:window 75}))
                [(weight-equal
                  [(if
                    (>
                     (moving-average-return "QQQ" {:window 60})
                     (moving-average-return "IWM" {:window 100}))
                    [(asset
                      "BTAL"
                      "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "DIA" {:window 55})
                         (cumulative-return "IWM" {:window 40}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "EFA" {:window 20})
                             -8)
                            [(asset
                              "UGL"
                              "ProShares Trust - ProShares Ultra Gold 2x Shares")]
                            [(weight-equal
                              [(if
                                (>
                                 (stdev-return "EFA" {:window 50})
                                 (stdev-return "EFA" {:window 30}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "IWM"
                                      {:window 70})
                                     (cumulative-return
                                      "SOXX"
                                      {:window 50}))
                                    [(asset
                                      "SOXL"
                                      "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                                    [(weight-equal
                                      [(asset
                                        "BIL"
                                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (stdev-return "EFA" {:window 50})
                             (stdev-return "EFA" {:window 30}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "IWM" {:window 70})
                                 (cumulative-return
                                  "SOXX"
                                  {:window 50}))
                                [(asset
                                  "SOXL"
                                  "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                                [(weight-equal
                                  [(asset
                                    "BIL"
                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "DIA" {:window 55})
                     (cumulative-return "IWM" {:window 40}))
                    [(weight-equal
                      [(if
                        (> (cumulative-return "EFA" {:window 20}) -8)
                        [(asset
                          "UGL"
                          "ProShares Trust - ProShares Ultra Gold 2x Shares")]
                        [(weight-equal
                          [(if
                            (>
                             (stdev-return "EFA" {:window 50})
                             (stdev-return "EFA" {:window 30}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "IWM" {:window 70})
                                 (cumulative-return
                                  "SOXX"
                                  {:window 50}))
                                [(asset
                                  "SOXL"
                                  "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                                [(weight-equal
                                  [(asset
                                    "BIL"
                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (stdev-return "EFA" {:window 50})
                         (stdev-return "EFA" {:window 30}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "IWM" {:window 70})
                             (cumulative-return "SOXX" {:window 50}))
                            [(asset
                              "SOXL"
                              "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                            [(weight-equal
                              [(asset
                                "BIL"
                                "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
           (group
            "Beam Filter: HYG, BTAL 28/9.5"
            [(weight-equal
              [(if
                (>
                 (stdev-return "IWM" {:window 30})
                 (stdev-return "QQQ" {:window 40}))
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "HYG" {:window 75})
                     (cumulative-return "QQQ" {:window 5}))
                    [(asset
                      "HYG"
                      "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "QQQ" {:window 5})
                         (cumulative-return "HYG" {:window 55}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "IWM" {:window 85})
                             (cumulative-return "BTAL" {:window 65}))
                            [(asset
                              "BTAL"
                              "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return
                                  "BTAL"
                                  {:window 60})
                                 (cumulative-return
                                  "BTAL"
                                  {:window 55}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "BTAL"
                                      {:window 90})
                                     (cumulative-return
                                      "IWM"
                                      {:window 10}))
                                    [(asset
                                      "HYG"
                                      "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                                    [(weight-equal
                                      [(asset
                                        "BIL"
                                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "BTAL" {:window 60})
                             (cumulative-return "BTAL" {:window 55}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return
                                  "BTAL"
                                  {:window 90})
                                 (cumulative-return
                                  "IWM"
                                  {:window 10}))
                                [(asset
                                  "HYG"
                                  "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                                [(weight-equal
                                  [(asset
                                    "BIL"
                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "QQQ" {:window 5})
                     (cumulative-return "HYG" {:window 55}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "IWM" {:window 85})
                         (cumulative-return "BTAL" {:window 65}))
                        [(asset
                          "BTAL"
                          "AGF Investments Trust - AGF U.S. Market Neutral Anti-Beta Fund")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "BTAL" {:window 60})
                             (cumulative-return "BTAL" {:window 55}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return
                                  "BTAL"
                                  {:window 90})
                                 (cumulative-return
                                  "IWM"
                                  {:window 10}))
                                [(asset
                                  "HYG"
                                  "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                                [(weight-equal
                                  [(asset
                                    "BIL"
                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "BTAL" {:window 60})
                         (cumulative-return "BTAL" {:window 55}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "BTAL" {:window 90})
                             (cumulative-return "IWM" {:window 10}))
                            [(asset
                              "HYG"
                              "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD High Yield Corporate Bond ETF")]
                            [(weight-equal
                              [(asset
                                "BIL"
                                "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
           (group
            "Beam Filter: BITO, IEF 85/23"
            [(weight-equal
              [(if
                (>
                 (cumulative-return "EWG" {:window 45})
                 (cumulative-return "XLI" {:window 75}))
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "EFA" {:window 55})
                     (cumulative-return "TLT" {:window 75}))
                    [(asset
                      "IEF"
                      "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "XLY" {:window 45})
                         (cumulative-return "IWM" {:window 35}))
                        [(weight-equal
                          [(if
                            (>
                             (stdev-return "XLF" {:window 10})
                             (stdev-return "XLF" {:window 40}))
                            [(asset
                              "BITO"
                              "ProShares Trust - ProShares Bitcoin ETF")]
                            [(weight-equal
                              [(if
                                (>
                                 (moving-average-return
                                  "HYG"
                                  {:window 90})
                                 (moving-average-return
                                  "SHY"
                                  {:window 90}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (stdev-return "IWM" {:window 30})
                                     (stdev-return "IWM" {:window 40}))
                                    [(asset
                                      "IEF"
                                      "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (moving-average-return "HYG" {:window 90})
                             (moving-average-return
                              "SHY"
                              {:window 90}))
                            [(weight-equal
                              [(if
                                (>
                                 (stdev-return "IWM" {:window 30})
                                 (stdev-return "IWM" {:window 40}))
                                [(asset
                                  "IEF"
                                  "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "XLY" {:window 45})
                     (cumulative-return "IWM" {:window 35}))
                    [(weight-equal
                      [(if
                        (>
                         (stdev-return "XLF" {:window 10})
                         (stdev-return "XLF" {:window 40}))
                        [(asset
                          "BITO"
                          "ProShares Trust - ProShares Bitcoin ETF")]
                        [(weight-equal
                          [(if
                            (>
                             (moving-average-return "HYG" {:window 90})
                             (moving-average-return
                              "SHY"
                              {:window 90}))
                            [(weight-equal
                              [(if
                                (>
                                 (stdev-return "IWM" {:window 30})
                                 (stdev-return "IWM" {:window 40}))
                                [(asset
                                  "IEF"
                                  "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (moving-average-return "HYG" {:window 90})
                         (moving-average-return "SHY" {:window 90}))
                        [(weight-equal
                          [(if
                            (>
                             (stdev-return "IWM" {:window 30})
                             (stdev-return "IWM" {:window 40}))
                            [(asset
                              "IEF"
                              "BlackRock Institutional Trust Company N.A. - iShares 7-10 Year Treasury Bond ETF")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])
           (group
            "Beam Filter: XLK, XLP, XLE 75/4.3"
            [(weight-equal
              [(if
                (>
                 (cumulative-return "IWM" {:window 5})
                 (cumulative-return "USO" {:window 5}))
                [(weight-equal
                  [(if
                    (>
                     (moving-average-return "XLI" {:window 20})
                     (moving-average-return "IWM" {:window 40}))
                    [(asset
                      "XLP"
                      "SSgA Active Trust - Consumer Staples Select Sector SPDR")]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "SOXX" {:window 65})
                         (cumulative-return "IWM" {:window 30}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "IWM" {:window 5})
                             (cumulative-return "XLE" {:window 10}))
                            [(asset
                              "XLE"
                              "SSgA Active Trust - The Energy Select Sector SPDR Fund")]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "XLI" {:window 80})
                                 (cumulative-return
                                  "XLE"
                                  {:window 30}))
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "DIA"
                                      {:window 30})
                                     (cumulative-return
                                      "USO"
                                      {:window 60}))
                                    [(asset
                                      "XLK"
                                      "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                                    [(asset
                                      "BIL"
                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "XLI" {:window 80})
                             (cumulative-return "XLE" {:window 30}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "DIA" {:window 30})
                                 (cumulative-return
                                  "USO"
                                  {:window 60}))
                                [(asset
                                  "XLK"
                                  "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])]
                [(weight-equal
                  [(if
                    (>
                     (cumulative-return "SOXX" {:window 65})
                     (cumulative-return "IWM" {:window 30}))
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "IWM" {:window 5})
                         (cumulative-return "XLE" {:window 10}))
                        [(asset
                          "XLE"
                          "SSgA Active Trust - The Energy Select Sector SPDR Fund")]
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "XLI" {:window 80})
                             (cumulative-return "XLE" {:window 30}))
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "DIA" {:window 30})
                                 (cumulative-return
                                  "USO"
                                  {:window 60}))
                                [(asset
                                  "XLK"
                                  "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                                [(asset
                                  "BIL"
                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                    [(weight-equal
                      [(if
                        (>
                         (cumulative-return "XLI" {:window 80})
                         (cumulative-return "XLE" {:window 30}))
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "DIA" {:window 30})
                             (cumulative-return "USO" {:window 60}))
                            [(asset
                              "XLK"
                              "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])]))
