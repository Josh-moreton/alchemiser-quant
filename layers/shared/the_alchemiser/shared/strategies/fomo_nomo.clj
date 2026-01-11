(defsymphony
 "FOMO NOMO - No Leverage"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
    (> (current-price "VTI") (moving-average-price "VTI" {:window 60}))
    [(weight-equal
      [(filter
        (rsi {:window 7})
        (select-bottom 2)
        [(weight-equal
          [(filter
            (cumulative-return {:window 2})
            (select-top 5)
            [(asset "NVDA" "NVIDIA Corp")
             (asset "AMD" "Advanced Micro Devices Inc.")
             (asset "INTC" "Intel Corp.")
             (asset "TSM" "Taiwan Semiconductor Manufacturing - ADR")
             (asset "AVGO" "Broadcom Inc")
             (asset "MU" "Micron Technology Inc.")
             (asset "QCOM" "Qualcomm, Inc.")
             (asset "MRVL" "Marvell Technology Inc")
             (asset "ARM" "Arm Holdings plc. - ADR")
             (asset "AMAT" "Applied Materials Inc.")
             (asset "LRCX" "Lam Research Corp.")
             (asset "ALAB" "Astera Labs Inc.")
             (asset "CRDO" "Credo Technology Group")
             (asset "ON" "ON Semiconductor Corp.")
             (asset "TXN" "Texas Instruments Inc.")
             (asset "MCHP" "Microchip Technology, Inc.")
             (asset "STM" "ST Microelectronics")
             (asset "GFS" "GlobalFoundries Inc")
             (asset "DIOD" "Diodes, Inc.")
             (asset "POWI" "Power Integrations Inc.")
             (asset "SIMO" "Silicon Motion Technology Corp - ADR")
             (asset "POET" "POET Technologies Inc")
             (asset "SKYT" "SkyWater Technology Inc")
             (asset "CAMT" "Camtek Ltd")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "IONQ" "IonQ Inc")
             (asset "RGTI" "Rigetti Computing Inc")
             (asset "QBTS" "D-Wave Quantum Inc")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "PLTR" "Palantir Technologies Inc")
             (asset "APP" "Applovin Corp")
             (asset "SOUN" "SoundHound AI Inc")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "INOD" "Innodata Inc")
             (asset "TEM" "Tempus AI Inc.")
             (asset
              "QSI"
              "Quantum-Si Incorporated - Ordinary Shares - Class A")
             (asset "NBIS" "Nebius Group N.V.")
             (asset "CRM" "Salesforce Inc")
             (asset "SNOW" "Snowflake Inc")
             (asset "DDOG" "Datadog Inc - Ordinary Shares - Class A")
             (asset "MDB" "MongoDB Inc - Ordinary Shares - Class A")
             (asset "PATH" "UiPath Inc - Ordinary Shares - Class A")
             (asset "CFLT" "Confluent Inc - Ordinary Shares Class A")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "RDDT" "Reddit Inc. - Ordinary Shares - Class A")
             (asset "DUOL" "Duolingo Inc - Ordinary Shares - Class A")
             (asset "NOW" "ServiceNow Inc")
             (asset "PYPL" "PayPal Holdings Inc")
             (asset "AMPL" "Amplitude Inc - Ordinary Shares - Class A")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ORCL" "Oracle Corp.")
             (asset
              "CRWD"
              "Crowdstrike Holdings Inc - Ordinary Shares - Class A")
             (asset "PANW" "Palo Alto Networks Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc - Ordinary Shares - Class A")
             (asset "FTNT" "Fortinet Inc")
             (asset "NET" "Cloudflare Inc - Ordinary Shares - Class A")
             (asset "MSFT" "Microsoft Corporation")
             (asset "AAPL" "Apple Inc")
             (asset "GOOGL" "Alphabet Inc - Ordinary Shares - Class A")
             (asset "AMZN" "Amazon.com Inc.")
             (asset
              "META"
              "Meta Platforms Inc - Ordinary Shares - Class A")
             (asset "IBM" "International Business Machines Corp.")
             (asset "SMCI" "Super Micro Computer Inc")
             (asset "VRT" "Vertiv Holdings")
             (asset "CLS" "Celestica Inc")
             (asset "APH" "Amphenol Corp")
             (asset
              "DELL"
              "Dell Technologies Inc - Ordinary Shares - Class C")
             (asset "HPE" "Hewlett Packard Enterprise Co")
             (asset "ANET" "Arista Networks Inc")
             (asset "EQIX" "Equinix Inc")
             (asset "DLR" "Digital Realty Trust Inc")
             (asset "IRM" "Iron Mountain Inc.")
             (asset "ETN" "Eaton Corp PLC")
             (asset "HUBB" "Hubbell Inc")
             (asset "FLEX" "Flex Ltd")
             (asset "NVT" "nVent Electric PLC")
             (asset "LUMN" "Lumen Technologies Inc")
             (asset "SANM" "Sanmina Corp")
             (asset "FN" "Fabrinet")
             (asset "POWL" "Powell Industries, Inc.")
             (asset "STX" "Seagate Technology Holdings")
             (asset "WDC" "Western Digital Corp.")
             (asset "MSTR" "Strategy Inc. (MicroStrategy)")
             (asset "COIN" "Coinbase Global Inc")
             (asset "HOOD" "Robinhood Markets Inc")
             (asset "XYZ" "Block Inc")
             (asset "GLXY" "Galaxy Digital Inc.")
             (asset "MARA" "MARA Holdings Inc.")
             (asset "RIOT" "Riot Platforms Inc")
             (asset "CLSK" "Cleanspark Inc")
             (asset "CORZ" "Core Scientific Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "CIFR" "Cipher Mining Inc")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "WULF" "TeraWulf Inc")
             (asset "IREN" "IREN Ltd.")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "BITI"
              "ProShares Trust - ProShares Short Bitcoin ETF")
             (asset "ISRG" "Intuitive Surgical Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "RKLB" "Rocket Lab USA Inc")
             (asset "ASTS" "AST SpaceMobile Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset
              "SATL"
              "Satellogic Inc - Ordinary Shares - Class A")
             (asset
              "SIDU"
              "Sidus Space Inc - Ordinary Shares - Class A")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "JOBY" "Joby Aviation Inc")
             (asset "ACHR" "Archer Aviation Inc")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "BA" "Boeing Co.")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset
              "CACI"
              "Caci International Inc. - Registered Shares - Class A")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "KTOS" "Kratos Defense & Security")
             (asset "AVAV" "AeroVironment Inc.")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "KOPN" "Kopin Corp.")
             (asset "ITA" "iShares U.S. Aerospace & Defense ETF")
             (asset "CCJ" "Cameco Corp")
             (asset "OKLO" "Oklo Inc")
             (asset "SMR" "NuScale Power Corporation")
             (asset "NNE" "Nano Nuclear Energy Inc")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Funds - Global X Uranium ETF")
             (asset "CEG" "Constellation Energy Corporation")
             (asset "VST" "Vistra Corp")
             (asset "GEV" "GE Vernova Inc.")
             (asset "TLN" "Talen Energy Corp")
             (asset "NEE" "NextEra Energy Inc")
             (asset "NRG" "NRG Energy Inc.")
             (asset "AES" "AES Corp.")
             (asset "ETR" "Entergy Corp.")
             (asset "IDA" "Idacorp, Inc.")
             (asset "DUK" "Duke Energy Corp.")
             (asset "SO" "Southern Company")
             (asset "PNW" "Pinnacle West Capital Corp.")
             (asset "D" "Dominion Energy Inc")
             (asset "WMB" "Williams Cos Inc")
             (asset
              "KMI"
              "Kinder Morgan Inc - Ordinary Shares - Class P")
             (asset "ET" "Energy Transfer LP - Unit")
             (asset "CMI" "Cummins Inc")
             (asset "PWR" "Quanta Services, Inc.")
             (asset "EME" "Emcor Group, Inc.")
             (asset "MTZ" "Mastec Inc.")
             (asset "DY" "Dycom Industries, Inc.")
             (asset "MYRG" "MYR Group Inc")
             (asset "FLR" "Fluor Corporation")
             (asset "TTEK" "Tetra Tech, Inc.")
             (asset "AGX" "Argan Inc")
             (asset "STRL" "Sterling Infrastructure Inc")
             (asset "FIX" "Comfort Systems USA, Inc.")
             (asset "APG" "APi Group Corporation")
             (asset "ENPH" "Enphase Energy Inc")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset
              "CWEN"
              "Clearway Energy Inc - Ordinary Shares - Class C")
             (asset "AMRC" "Ameresco Inc. - Ordinary Shares - Class A")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "BE" "Bloom Energy Corp")
             (asset "GEVO" "Gevo Inc")
             (asset "QS" "QuantumScape Corp")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset
              "RIVN"
              "Rivian Automotive Inc - Ordinary Shares - Class A")
             (asset
              "HYLN"
              "Hyliion Holdings Corporation - Ordinary Shares - Class A")
             (asset "XOM" "Exxon Mobil Corp.")
             (asset "CVX" "Chevron Corp.")
             (asset "OXY" "Occidental Petroleum Corp.")
             (asset "DVN" "Devon Energy Corp.")
             (asset "EOG" "EOG Resources, Inc.")
             (asset "COP" "Conoco Phillips")
             (asset
              "HESM"
              "Hess Midstream LP - Ordinary Shares - Class A")
             (asset "MPC" "Marathon Petroleum Corp")
             (asset "VLO" "Valero Energy Corp.")
             (asset "PSX" "Phillips 66")
             (asset "SLB" "SLB Ltd.")
             (asset "HAL" "Halliburton Co.")
             (asset "BTU" "Peabody Energy Corp. - Ordinary Shares New")
             (asset "PBF" "PBF Energy Inc - Ordinary Shares - Class A")
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset
              "DNA"
              "Ginkgo Bioworks Holdings Inc - Ordinary Shares - Class A")
             (asset "ARCT" "Arcturus Therapeutics Holdings Inc")
             (asset "CRBU" "Caribou Biosciences Inc")
             (asset "WVE" "Wave Life Sciences Ltd.")
             (asset "RXRX" "Recursion Pharmaceuticals Inc")
             (asset "ALNY" "Alnylam Pharmaceuticals Inc")
             (asset "IONS" "Ionis Pharmaceuticals Inc")
             (asset "SRPT" "Sarepta Therapeutics Inc")
             (asset "RNA" "Avidity Biosciences Inc")
             (asset "QURE" "uniQure N.V.")
             (asset "RLAY" "Relay Therapeutics Inc")
             (asset "SLDB" "Solid Biosciences Inc")
             (asset "AUTL" "Autolus Therapeutics plc - ADR")
             (asset "VKTX" "Viking Therapeutics Inc")
             (asset "MDGL" "Madrigal Pharmaceuticals Inc")
             (asset "AXSM" "Axsome Therapeutics Inc")
             (asset "PCVX" "Vaxcyte Inc")
             (asset "CYTK" "Cytokinetics Inc")
             (asset "CRNX" "Crinetics Pharmaceuticals Inc")
             (asset "DVAX" "Dynavax Technologies Corp.")
             (asset "FATE" "Fate Therapeutics Inc")
             (asset "PRAX" "Praxis Precision Medicines Inc")
             (asset "KROS" "Keros Therapeutics Inc")
             (asset "IMNM" "Immunome Inc")
             (asset "PLRX" "Pliant Therapeutics Inc")
             (asset "MIRM" "Mirum Pharmaceuticals Inc")
             (asset "CNTA" "Centessa Pharmaceuticals plc - ADR")
             (asset "XERS" "Xeris Biopharma Holdings Inc")
             (asset "ZYME" "Zymeworks BC Inc")
             (asset "RAPT" "RAPT Therapeutics Inc")
             (asset "CELC" "Celcuity Inc")
             (asset "ABVX" "Abivax - ADR")
             (asset "MNMD" "Mind Medicine Inc")
             (asset "XFOR" "X4 Pharmaceuticals Inc")
             (asset "PLSE" "Pulse Biosciences Inc")
             (asset "CGEM" "Cullinan Therapeutics Inc")
             (asset
              "QNTM"
              "Quantum BioPharma Ltd. - Ordinary Shares - Class B (Sub Voting)")
             (asset "ALT" "Altimmune Inc")
             (asset "TERN" "Terns Pharmaceuticals Inc")
             (asset "ARQT" "Arcutis Biotherapeutics Inc")
             (asset "ACLX" "Arcellx Inc")
             (asset "OLMA" "Olema Pharmaceuticals Inc")
             (asset "VTYX" "Ventyx Biosciences Inc")
             (asset "ABSI" "Absci Corp")
             (asset "AVXL" "Anavex Life Sciences Corp")
             (asset "RZLT" "Rezolute Inc")
             (asset "TIL" "Instil Bio Inc")
             (asset "NRSN" "NeuroSense Therapeutics Ltd")
             (asset "SAVA" "Cassava Sciences Inc")
             (asset "ABCL" "AbCellera Biologics Inc")
             (asset "EVO" "Evotec SE - ADR")
             (asset "SLP" "Simulations Plus Inc.")
             (asset "GHRS" "GH Research PLC")
             (asset "DXCM" "Dexcom Inc")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset
              "BFLY"
              "Butterfly Network Inc - Ordinary Shares - Class A")
             (asset "ALIT" "Alight Inc. - Ordinary Shares - Class A")
             (asset "WELL" "Welltower Inc.")
             (asset "LLY" "Lilly(Eli) & Co")
             (asset "UNH" "Unitedhealth Group Inc")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "B" "Barrick Mining Corp.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDX" "VanEck Gold Miners ETF")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SLV" "iShares Silver Trust")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "MP" "MP Materials Corporation")
             (asset "LAC" "Lithium Americas Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset
              "TECK"
              "Teck Resources Ltd - Ordinary Shares - Class B (Sub Voting)")
             (asset "UAMY" "United States Antimony Corp")
             (asset "CPER" "United States Copper Index")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "VMC" "Vulcan Materials Co")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "SOFI" "SoFi Technologies Inc")
             (asset "AFRM" "Affirm Holdings Inc")
             (asset "UPST" "Upstart Holdings Inc")
             (asset "NU" "Nu Holdings Ltd")
             (asset "OPEN" "Opendoor Technologies Inc")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset
              "GRAB"
              "Grab Holdings Limited - Ordinary Shares - Class A")
             (asset
              "DKNG"
              "DraftKings Inc. - Ordinary Shares - Class A")
             (asset "BABA" "Alibaba Group Holding Ltd")
             (asset "PDD" "PDD Holdings Inc - ADR")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset
              "JCI"
              "Johnson Controls International plc - Registered Shares")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset
              "LPTH"
              "Lightpath Technologies, Inc. - Ordinary Shares - Class A")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset
              "PSTL"
              "Postal Realty Trust Inc - Ordinary Shares - Class A")
             (asset "CAVA" "Cava Group Inc")
             (asset
              "SMH"
              "VanEck ETF Trust - VanEck Semiconductor ETF")
             (asset
              "XLK"
              "SSgA Active Trust - State Street Technology Select Sector SPDR ETF")
             (asset
              "XLI"
              "SSgA Active Trust - State Street Industrial Select Sector SPDR ETF")
             (asset
              "XME"
              "SPDR Series Trust - State Street SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BKKT"
              "Bakkt Holdings Inc. - Ordinary Shares - Class A")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "EVTL" "Vertical Aerospace Ltd")
             (asset "QUBT" "Quantum Computing Inc")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset "BMNR" "BitMine Immersion Technologies Inc")
             (asset
              "KWEB"
              "KraneShares Trust - KraneShares CSI China Internet ETF")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "REKT"
              "Direxion Shares ETF Trust - Direxion Daily Crypto Industry Bear 1X Shares")
             (asset
              "ETH"
              "Grayscale Ethereum Staking Mini ETF - Common units of fractional undivided beneficial interest")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "SRE" "Sempra")
             (asset
              "TSLS"
              "Direxion Shares ETF Trust - Direxion Daily TSLA Bear 1X Shares")
             (asset "TSLA" "Tesla Inc")
             (asset "AAON" "AAON Inc.")
             (asset "APD" "Air Products & Chemicals Inc.")
             (asset "EQT" "EQT Corp")
             (asset "TMC" "TMC the metals company Inc")
             (asset "CSCO" "Cisco Systems, Inc.")
             (asset
              "SLVP"
              "BlackRock Institutional Trust Company N.A. - iShares MSCI Global Silver and Metals Miners ETF")])])
         (weight-equal
          [(filter
            (stdev-return {:window 2})
            (select-top 5)
            [(asset "NVDA" "NVIDIA Corp")
             (asset "AMD" "Advanced Micro Devices Inc.")
             (asset "INTC" "Intel Corp.")
             (asset "TSM" "Taiwan Semiconductor Manufacturing - ADR")
             (asset "AVGO" "Broadcom Inc")
             (asset "MU" "Micron Technology Inc.")
             (asset "QCOM" "Qualcomm, Inc.")
             (asset "MRVL" "Marvell Technology Inc")
             (asset "ARM" "Arm Holdings plc. - ADR")
             (asset "AMAT" "Applied Materials Inc.")
             (asset "LRCX" "Lam Research Corp.")
             (asset "ALAB" "Astera Labs Inc.")
             (asset "CRDO" "Credo Technology Group")
             (asset "ON" "ON Semiconductor Corp.")
             (asset "TXN" "Texas Instruments Inc.")
             (asset "MCHP" "Microchip Technology, Inc.")
             (asset "STM" "ST Microelectronics")
             (asset "GFS" "GlobalFoundries Inc")
             (asset "DIOD" "Diodes, Inc.")
             (asset "POWI" "Power Integrations Inc.")
             (asset "SIMO" "Silicon Motion Technology Corp - ADR")
             (asset "POET" "POET Technologies Inc")
             (asset "SKYT" "SkyWater Technology Inc")
             (asset "CAMT" "Camtek Ltd")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "IONQ" "IonQ Inc")
             (asset "RGTI" "Rigetti Computing Inc")
             (asset "QBTS" "D-Wave Quantum Inc")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "PLTR" "Palantir Technologies Inc")
             (asset "APP" "Applovin Corp")
             (asset "SOUN" "SoundHound AI Inc")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "INOD" "Innodata Inc")
             (asset "TEM" "Tempus AI Inc.")
             (asset
              "QSI"
              "Quantum-Si Incorporated - Ordinary Shares - Class A")
             (asset "NBIS" "Nebius Group N.V.")
             (asset "CRM" "Salesforce Inc")
             (asset "SNOW" "Snowflake Inc")
             (asset "DDOG" "Datadog Inc - Ordinary Shares - Class A")
             (asset "MDB" "MongoDB Inc - Ordinary Shares - Class A")
             (asset "PATH" "UiPath Inc - Ordinary Shares - Class A")
             (asset "CFLT" "Confluent Inc - Ordinary Shares Class A")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "RDDT" "Reddit Inc. - Ordinary Shares - Class A")
             (asset "DUOL" "Duolingo Inc - Ordinary Shares - Class A")
             (asset "NOW" "ServiceNow Inc")
             (asset "PYPL" "PayPal Holdings Inc")
             (asset "AMPL" "Amplitude Inc - Ordinary Shares - Class A")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ORCL" "Oracle Corp.")
             (asset
              "CRWD"
              "Crowdstrike Holdings Inc - Ordinary Shares - Class A")
             (asset "PANW" "Palo Alto Networks Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc - Ordinary Shares - Class A")
             (asset "FTNT" "Fortinet Inc")
             (asset "NET" "Cloudflare Inc - Ordinary Shares - Class A")
             (asset "MSFT" "Microsoft Corporation")
             (asset "AAPL" "Apple Inc")
             (asset "GOOGL" "Alphabet Inc - Ordinary Shares - Class A")
             (asset "AMZN" "Amazon.com Inc.")
             (asset
              "META"
              "Meta Platforms Inc - Ordinary Shares - Class A")
             (asset "IBM" "International Business Machines Corp.")
             (asset "SMCI" "Super Micro Computer Inc")
             (asset "VRT" "Vertiv Holdings")
             (asset "CLS" "Celestica Inc")
             (asset "APH" "Amphenol Corp")
             (asset
              "DELL"
              "Dell Technologies Inc - Ordinary Shares - Class C")
             (asset "HPE" "Hewlett Packard Enterprise Co")
             (asset "ANET" "Arista Networks Inc")
             (asset "EQIX" "Equinix Inc")
             (asset "DLR" "Digital Realty Trust Inc")
             (asset "IRM" "Iron Mountain Inc.")
             (asset "ETN" "Eaton Corp PLC")
             (asset "HUBB" "Hubbell Inc")
             (asset "FLEX" "Flex Ltd")
             (asset "NVT" "nVent Electric PLC")
             (asset "LUMN" "Lumen Technologies Inc")
             (asset "SANM" "Sanmina Corp")
             (asset "FN" "Fabrinet")
             (asset "POWL" "Powell Industries, Inc.")
             (asset "STX" "Seagate Technology Holdings")
             (asset "WDC" "Western Digital Corp.")
             (asset "MSTR" "Strategy Inc. (MicroStrategy)")
             (asset "COIN" "Coinbase Global Inc")
             (asset "HOOD" "Robinhood Markets Inc")
             (asset "XYZ" "Block Inc")
             (asset "GLXY" "Galaxy Digital Inc.")
             (asset "MARA" "MARA Holdings Inc.")
             (asset "RIOT" "Riot Platforms Inc")
             (asset "CLSK" "Cleanspark Inc")
             (asset "CORZ" "Core Scientific Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "CIFR" "Cipher Mining Inc")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "WULF" "TeraWulf Inc")
             (asset "IREN" "IREN Ltd.")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "BITI"
              "ProShares Trust - ProShares Short Bitcoin ETF")
             (asset "ISRG" "Intuitive Surgical Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "RKLB" "Rocket Lab USA Inc")
             (asset "ASTS" "AST SpaceMobile Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset
              "SATL"
              "Satellogic Inc - Ordinary Shares - Class A")
             (asset
              "SIDU"
              "Sidus Space Inc - Ordinary Shares - Class A")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "JOBY" "Joby Aviation Inc")
             (asset "ACHR" "Archer Aviation Inc")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "BA" "Boeing Co.")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset
              "CACI"
              "Caci International Inc. - Registered Shares - Class A")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "KTOS" "Kratos Defense & Security")
             (asset "AVAV" "AeroVironment Inc.")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "KOPN" "Kopin Corp.")
             (asset "ITA" "iShares U.S. Aerospace & Defense ETF")
             (asset "CCJ" "Cameco Corp")
             (asset "OKLO" "Oklo Inc")
             (asset "SMR" "NuScale Power Corporation")
             (asset "NNE" "Nano Nuclear Energy Inc")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Funds - Global X Uranium ETF")
             (asset "CEG" "Constellation Energy Corporation")
             (asset "VST" "Vistra Corp")
             (asset "GEV" "GE Vernova Inc.")
             (asset "TLN" "Talen Energy Corp")
             (asset "NEE" "NextEra Energy Inc")
             (asset "NRG" "NRG Energy Inc.")
             (asset "AES" "AES Corp.")
             (asset "ETR" "Entergy Corp.")
             (asset "IDA" "Idacorp, Inc.")
             (asset "DUK" "Duke Energy Corp.")
             (asset "SO" "Southern Company")
             (asset "PNW" "Pinnacle West Capital Corp.")
             (asset "D" "Dominion Energy Inc")
             (asset "WMB" "Williams Cos Inc")
             (asset
              "KMI"
              "Kinder Morgan Inc - Ordinary Shares - Class P")
             (asset "ET" "Energy Transfer LP - Unit")
             (asset "CMI" "Cummins Inc")
             (asset "PWR" "Quanta Services, Inc.")
             (asset "EME" "Emcor Group, Inc.")
             (asset "MTZ" "Mastec Inc.")
             (asset "DY" "Dycom Industries, Inc.")
             (asset "MYRG" "MYR Group Inc")
             (asset "FLR" "Fluor Corporation")
             (asset "TTEK" "Tetra Tech, Inc.")
             (asset "AGX" "Argan Inc")
             (asset "STRL" "Sterling Infrastructure Inc")
             (asset "FIX" "Comfort Systems USA, Inc.")
             (asset "APG" "APi Group Corporation")
             (asset "ENPH" "Enphase Energy Inc")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset
              "CWEN"
              "Clearway Energy Inc - Ordinary Shares - Class C")
             (asset "AMRC" "Ameresco Inc. - Ordinary Shares - Class A")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "BE" "Bloom Energy Corp")
             (asset "GEVO" "Gevo Inc")
             (asset "QS" "QuantumScape Corp")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset
              "RIVN"
              "Rivian Automotive Inc - Ordinary Shares - Class A")
             (asset
              "HYLN"
              "Hyliion Holdings Corporation - Ordinary Shares - Class A")
             (asset "XOM" "Exxon Mobil Corp.")
             (asset "CVX" "Chevron Corp.")
             (asset "OXY" "Occidental Petroleum Corp.")
             (asset "DVN" "Devon Energy Corp.")
             (asset "EOG" "EOG Resources, Inc.")
             (asset "COP" "Conoco Phillips")
             (asset
              "HESM"
              "Hess Midstream LP - Ordinary Shares - Class A")
             (asset "MPC" "Marathon Petroleum Corp")
             (asset "VLO" "Valero Energy Corp.")
             (asset "PSX" "Phillips 66")
             (asset "SLB" "SLB Ltd.")
             (asset "HAL" "Halliburton Co.")
             (asset "BTU" "Peabody Energy Corp. - Ordinary Shares New")
             (asset "PBF" "PBF Energy Inc - Ordinary Shares - Class A")
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset
              "DNA"
              "Ginkgo Bioworks Holdings Inc - Ordinary Shares - Class A")
             (asset "ARCT" "Arcturus Therapeutics Holdings Inc")
             (asset "CRBU" "Caribou Biosciences Inc")
             (asset "WVE" "Wave Life Sciences Ltd.")
             (asset "RXRX" "Recursion Pharmaceuticals Inc")
             (asset "ALNY" "Alnylam Pharmaceuticals Inc")
             (asset "IONS" "Ionis Pharmaceuticals Inc")
             (asset "SRPT" "Sarepta Therapeutics Inc")
             (asset "RNA" "Avidity Biosciences Inc")
             (asset "QURE" "uniQure N.V.")
             (asset "RLAY" "Relay Therapeutics Inc")
             (asset "SLDB" "Solid Biosciences Inc")
             (asset "AUTL" "Autolus Therapeutics plc - ADR")
             (asset "VKTX" "Viking Therapeutics Inc")
             (asset "MDGL" "Madrigal Pharmaceuticals Inc")
             (asset "AXSM" "Axsome Therapeutics Inc")
             (asset "PCVX" "Vaxcyte Inc")
             (asset "CYTK" "Cytokinetics Inc")
             (asset "CRNX" "Crinetics Pharmaceuticals Inc")
             (asset "DVAX" "Dynavax Technologies Corp.")
             (asset "FATE" "Fate Therapeutics Inc")
             (asset "PRAX" "Praxis Precision Medicines Inc")
             (asset "KROS" "Keros Therapeutics Inc")
             (asset "IMNM" "Immunome Inc")
             (asset "PLRX" "Pliant Therapeutics Inc")
             (asset "MIRM" "Mirum Pharmaceuticals Inc")
             (asset "CNTA" "Centessa Pharmaceuticals plc - ADR")
             (asset "XERS" "Xeris Biopharma Holdings Inc")
             (asset "ZYME" "Zymeworks BC Inc")
             (asset "RAPT" "RAPT Therapeutics Inc")
             (asset "CELC" "Celcuity Inc")
             (asset "ABVX" "Abivax - ADR")
             (asset "MNMD" "Mind Medicine Inc")
             (asset "XFOR" "X4 Pharmaceuticals Inc")
             (asset "PLSE" "Pulse Biosciences Inc")
             (asset "CGEM" "Cullinan Therapeutics Inc")
             (asset
              "QNTM"
              "Quantum BioPharma Ltd. - Ordinary Shares - Class B (Sub Voting)")
             (asset "ALT" "Altimmune Inc")
             (asset "TERN" "Terns Pharmaceuticals Inc")
             (asset "ARQT" "Arcutis Biotherapeutics Inc")
             (asset "ACLX" "Arcellx Inc")
             (asset "OLMA" "Olema Pharmaceuticals Inc")
             (asset "VTYX" "Ventyx Biosciences Inc")
             (asset "ABSI" "Absci Corp")
             (asset "AVXL" "Anavex Life Sciences Corp")
             (asset "RZLT" "Rezolute Inc")
             (asset "TIL" "Instil Bio Inc")
             (asset "NRSN" "NeuroSense Therapeutics Ltd")
             (asset "SAVA" "Cassava Sciences Inc")
             (asset "ABCL" "AbCellera Biologics Inc")
             (asset "EVO" "Evotec SE - ADR")
             (asset "SLP" "Simulations Plus Inc.")
             (asset "GHRS" "GH Research PLC")
             (asset "DXCM" "Dexcom Inc")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset
              "BFLY"
              "Butterfly Network Inc - Ordinary Shares - Class A")
             (asset "ALIT" "Alight Inc. - Ordinary Shares - Class A")
             (asset "WELL" "Welltower Inc.")
             (asset "LLY" "Lilly(Eli) & Co")
             (asset "UNH" "Unitedhealth Group Inc")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "B" "Barrick Mining Corp.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDX" "VanEck Gold Miners ETF")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SLV" "iShares Silver Trust")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "MP" "MP Materials Corporation")
             (asset "LAC" "Lithium Americas Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset
              "TECK"
              "Teck Resources Ltd - Ordinary Shares - Class B (Sub Voting)")
             (asset "UAMY" "United States Antimony Corp")
             (asset "CPER" "United States Copper Index")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "VMC" "Vulcan Materials Co")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "SOFI" "SoFi Technologies Inc")
             (asset "AFRM" "Affirm Holdings Inc")
             (asset "UPST" "Upstart Holdings Inc")
             (asset "NU" "Nu Holdings Ltd")
             (asset "OPEN" "Opendoor Technologies Inc")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset
              "GRAB"
              "Grab Holdings Limited - Ordinary Shares - Class A")
             (asset
              "DKNG"
              "DraftKings Inc. - Ordinary Shares - Class A")
             (asset "BABA" "Alibaba Group Holding Ltd")
             (asset "PDD" "PDD Holdings Inc - ADR")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset
              "JCI"
              "Johnson Controls International plc - Registered Shares")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset
              "LPTH"
              "Lightpath Technologies, Inc. - Ordinary Shares - Class A")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset
              "PSTL"
              "Postal Realty Trust Inc - Ordinary Shares - Class A")
             (asset "CAVA" "Cava Group Inc")
             (asset
              "SMH"
              "VanEck ETF Trust - VanEck Semiconductor ETF")
             (asset
              "XLK"
              "SSgA Active Trust - State Street Technology Select Sector SPDR ETF")
             (asset
              "XLI"
              "SSgA Active Trust - State Street Industrial Select Sector SPDR ETF")
             (asset
              "XME"
              "SPDR Series Trust - State Street SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BKKT"
              "Bakkt Holdings Inc. - Ordinary Shares - Class A")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "EVTL" "Vertical Aerospace Ltd")
             (asset "QUBT" "Quantum Computing Inc")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset "BMNR" "BitMine Immersion Technologies Inc")
             (asset
              "KWEB"
              "KraneShares Trust - KraneShares CSI China Internet ETF")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "REKT"
              "Direxion Shares ETF Trust - Direxion Daily Crypto Industry Bear 1X Shares")
             (asset
              "ETH"
              "Grayscale Ethereum Staking Mini ETF - Common units of fractional undivided beneficial interest")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "SRE" "Sempra")
             (asset
              "TSLS"
              "Direxion Shares ETF Trust - Direxion Daily TSLA Bear 1X Shares")
             (asset "TSLA" "Tesla Inc")
             (asset "AAON" "AAON Inc.")
             (asset "APD" "Air Products & Chemicals Inc.")
             (asset "EQT" "EQT Corp")
             (asset "TMC" "TMC the metals company Inc")
             (asset "CSCO" "Cisco Systems, Inc.")
             (asset
              "SLVP"
              "BlackRock Institutional Trust Company N.A. - iShares MSCI Global Silver and Metals Miners ETF")])])
         (weight-equal
          [(filter
            (stdev-return {:window 2})
            (select-top 3)
            [(asset "NVDA" "NVIDIA Corp")
             (asset "AMD" "Advanced Micro Devices Inc.")
             (asset "INTC" "Intel Corp.")
             (asset "TSM" "Taiwan Semiconductor Manufacturing - ADR")
             (asset "AVGO" "Broadcom Inc")
             (asset "MU" "Micron Technology Inc.")
             (asset "QCOM" "Qualcomm, Inc.")
             (asset "MRVL" "Marvell Technology Inc")
             (asset "ARM" "Arm Holdings plc. - ADR")
             (asset "AMAT" "Applied Materials Inc.")
             (asset "LRCX" "Lam Research Corp.")
             (asset "ALAB" "Astera Labs Inc.")
             (asset "CRDO" "Credo Technology Group")
             (asset "ON" "ON Semiconductor Corp.")
             (asset "TXN" "Texas Instruments Inc.")
             (asset "MCHP" "Microchip Technology, Inc.")
             (asset "STM" "ST Microelectronics")
             (asset "GFS" "GlobalFoundries Inc")
             (asset "DIOD" "Diodes, Inc.")
             (asset "POWI" "Power Integrations Inc.")
             (asset "SIMO" "Silicon Motion Technology Corp - ADR")
             (asset "POET" "POET Technologies Inc")
             (asset "SKYT" "SkyWater Technology Inc")
             (asset "CAMT" "Camtek Ltd")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "IONQ" "IonQ Inc")
             (asset "RGTI" "Rigetti Computing Inc")
             (asset "QBTS" "D-Wave Quantum Inc")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "PLTR" "Palantir Technologies Inc")
             (asset "APP" "Applovin Corp")
             (asset "SOUN" "SoundHound AI Inc")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "INOD" "Innodata Inc")
             (asset "TEM" "Tempus AI Inc.")
             (asset
              "QSI"
              "Quantum-Si Incorporated - Ordinary Shares - Class A")
             (asset "NBIS" "Nebius Group N.V.")
             (asset "CRM" "Salesforce Inc")
             (asset "SNOW" "Snowflake Inc")
             (asset "DDOG" "Datadog Inc - Ordinary Shares - Class A")
             (asset "MDB" "MongoDB Inc - Ordinary Shares - Class A")
             (asset "PATH" "UiPath Inc - Ordinary Shares - Class A")
             (asset "CFLT" "Confluent Inc - Ordinary Shares Class A")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "RDDT" "Reddit Inc. - Ordinary Shares - Class A")
             (asset "DUOL" "Duolingo Inc - Ordinary Shares - Class A")
             (asset "NOW" "ServiceNow Inc")
             (asset "PYPL" "PayPal Holdings Inc")
             (asset "AMPL" "Amplitude Inc - Ordinary Shares - Class A")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ORCL" "Oracle Corp.")
             (asset
              "CRWD"
              "Crowdstrike Holdings Inc - Ordinary Shares - Class A")
             (asset "PANW" "Palo Alto Networks Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc - Ordinary Shares - Class A")
             (asset "FTNT" "Fortinet Inc")
             (asset "NET" "Cloudflare Inc - Ordinary Shares - Class A")
             (asset "MSFT" "Microsoft Corporation")
             (asset "AAPL" "Apple Inc")
             (asset "GOOGL" "Alphabet Inc - Ordinary Shares - Class A")
             (asset "AMZN" "Amazon.com Inc.")
             (asset
              "META"
              "Meta Platforms Inc - Ordinary Shares - Class A")
             (asset "IBM" "International Business Machines Corp.")
             (asset "SMCI" "Super Micro Computer Inc")
             (asset "VRT" "Vertiv Holdings")
             (asset "CLS" "Celestica Inc")
             (asset "APH" "Amphenol Corp")
             (asset
              "DELL"
              "Dell Technologies Inc - Ordinary Shares - Class C")
             (asset "HPE" "Hewlett Packard Enterprise Co")
             (asset "ANET" "Arista Networks Inc")
             (asset "EQIX" "Equinix Inc")
             (asset "DLR" "Digital Realty Trust Inc")
             (asset "IRM" "Iron Mountain Inc.")
             (asset "ETN" "Eaton Corp PLC")
             (asset "HUBB" "Hubbell Inc")
             (asset "FLEX" "Flex Ltd")
             (asset "NVT" "nVent Electric PLC")
             (asset "LUMN" "Lumen Technologies Inc")
             (asset "SANM" "Sanmina Corp")
             (asset "FN" "Fabrinet")
             (asset "POWL" "Powell Industries, Inc.")
             (asset "STX" "Seagate Technology Holdings")
             (asset "WDC" "Western Digital Corp.")
             (asset "MSTR" "Strategy Inc. (MicroStrategy)")
             (asset "COIN" "Coinbase Global Inc")
             (asset "HOOD" "Robinhood Markets Inc")
             (asset "XYZ" "Block Inc")
             (asset "GLXY" "Galaxy Digital Inc.")
             (asset "MARA" "MARA Holdings Inc.")
             (asset "RIOT" "Riot Platforms Inc")
             (asset "CLSK" "Cleanspark Inc")
             (asset "CORZ" "Core Scientific Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "CIFR" "Cipher Mining Inc")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "WULF" "TeraWulf Inc")
             (asset "IREN" "IREN Ltd.")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "BITI"
              "ProShares Trust - ProShares Short Bitcoin ETF")
             (asset "ISRG" "Intuitive Surgical Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "RKLB" "Rocket Lab USA Inc")
             (asset "ASTS" "AST SpaceMobile Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset
              "SATL"
              "Satellogic Inc - Ordinary Shares - Class A")
             (asset
              "SIDU"
              "Sidus Space Inc - Ordinary Shares - Class A")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "JOBY" "Joby Aviation Inc")
             (asset "ACHR" "Archer Aviation Inc")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "BA" "Boeing Co.")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset
              "CACI"
              "Caci International Inc. - Registered Shares - Class A")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "KTOS" "Kratos Defense & Security")
             (asset "AVAV" "AeroVironment Inc.")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "KOPN" "Kopin Corp.")
             (asset "ITA" "iShares U.S. Aerospace & Defense ETF")
             (asset "CCJ" "Cameco Corp")
             (asset "OKLO" "Oklo Inc")
             (asset "SMR" "NuScale Power Corporation")
             (asset "NNE" "Nano Nuclear Energy Inc")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Funds - Global X Uranium ETF")
             (asset "CEG" "Constellation Energy Corporation")
             (asset "VST" "Vistra Corp")
             (asset "GEV" "GE Vernova Inc.")
             (asset "TLN" "Talen Energy Corp")
             (asset "NEE" "NextEra Energy Inc")
             (asset "NRG" "NRG Energy Inc.")
             (asset "AES" "AES Corp.")
             (asset "ETR" "Entergy Corp.")
             (asset "IDA" "Idacorp, Inc.")
             (asset "DUK" "Duke Energy Corp.")
             (asset "SO" "Southern Company")
             (asset "PNW" "Pinnacle West Capital Corp.")
             (asset "D" "Dominion Energy Inc")
             (asset "WMB" "Williams Cos Inc")
             (asset
              "KMI"
              "Kinder Morgan Inc - Ordinary Shares - Class P")
             (asset "ET" "Energy Transfer LP - Unit")
             (asset "CMI" "Cummins Inc")
             (asset "PWR" "Quanta Services, Inc.")
             (asset "EME" "Emcor Group, Inc.")
             (asset "MTZ" "Mastec Inc.")
             (asset "DY" "Dycom Industries, Inc.")
             (asset "MYRG" "MYR Group Inc")
             (asset "FLR" "Fluor Corporation")
             (asset "TTEK" "Tetra Tech, Inc.")
             (asset "AGX" "Argan Inc")
             (asset "STRL" "Sterling Infrastructure Inc")
             (asset "FIX" "Comfort Systems USA, Inc.")
             (asset "APG" "APi Group Corporation")
             (asset "ENPH" "Enphase Energy Inc")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset
              "CWEN"
              "Clearway Energy Inc - Ordinary Shares - Class C")
             (asset "AMRC" "Ameresco Inc. - Ordinary Shares - Class A")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "BE" "Bloom Energy Corp")
             (asset "GEVO" "Gevo Inc")
             (asset "QS" "QuantumScape Corp")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset
              "RIVN"
              "Rivian Automotive Inc - Ordinary Shares - Class A")
             (asset
              "HYLN"
              "Hyliion Holdings Corporation - Ordinary Shares - Class A")
             (asset "XOM" "Exxon Mobil Corp.")
             (asset "CVX" "Chevron Corp.")
             (asset "OXY" "Occidental Petroleum Corp.")
             (asset "DVN" "Devon Energy Corp.")
             (asset "EOG" "EOG Resources, Inc.")
             (asset "COP" "Conoco Phillips")
             (asset
              "HESM"
              "Hess Midstream LP - Ordinary Shares - Class A")
             (asset "MPC" "Marathon Petroleum Corp")
             (asset "VLO" "Valero Energy Corp.")
             (asset "PSX" "Phillips 66")
             (asset "SLB" "SLB Ltd.")
             (asset "HAL" "Halliburton Co.")
             (asset "BTU" "Peabody Energy Corp. - Ordinary Shares New")
             (asset "PBF" "PBF Energy Inc - Ordinary Shares - Class A")
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset
              "DNA"
              "Ginkgo Bioworks Holdings Inc - Ordinary Shares - Class A")
             (asset "ARCT" "Arcturus Therapeutics Holdings Inc")
             (asset "CRBU" "Caribou Biosciences Inc")
             (asset "WVE" "Wave Life Sciences Ltd.")
             (asset "RXRX" "Recursion Pharmaceuticals Inc")
             (asset "ALNY" "Alnylam Pharmaceuticals Inc")
             (asset "IONS" "Ionis Pharmaceuticals Inc")
             (asset "SRPT" "Sarepta Therapeutics Inc")
             (asset "RNA" "Avidity Biosciences Inc")
             (asset "QURE" "uniQure N.V.")
             (asset "RLAY" "Relay Therapeutics Inc")
             (asset "SLDB" "Solid Biosciences Inc")
             (asset "AUTL" "Autolus Therapeutics plc - ADR")
             (asset "VKTX" "Viking Therapeutics Inc")
             (asset "MDGL" "Madrigal Pharmaceuticals Inc")
             (asset "AXSM" "Axsome Therapeutics Inc")
             (asset "PCVX" "Vaxcyte Inc")
             (asset "CYTK" "Cytokinetics Inc")
             (asset "CRNX" "Crinetics Pharmaceuticals Inc")
             (asset "DVAX" "Dynavax Technologies Corp.")
             (asset "FATE" "Fate Therapeutics Inc")
             (asset "PRAX" "Praxis Precision Medicines Inc")
             (asset "KROS" "Keros Therapeutics Inc")
             (asset "IMNM" "Immunome Inc")
             (asset "PLRX" "Pliant Therapeutics Inc")
             (asset "MIRM" "Mirum Pharmaceuticals Inc")
             (asset "CNTA" "Centessa Pharmaceuticals plc - ADR")
             (asset "XERS" "Xeris Biopharma Holdings Inc")
             (asset "ZYME" "Zymeworks BC Inc")
             (asset "RAPT" "RAPT Therapeutics Inc")
             (asset "CELC" "Celcuity Inc")
             (asset "ABVX" "Abivax - ADR")
             (asset "MNMD" "Mind Medicine Inc")
             (asset "XFOR" "X4 Pharmaceuticals Inc")
             (asset "PLSE" "Pulse Biosciences Inc")
             (asset "CGEM" "Cullinan Therapeutics Inc")
             (asset
              "QNTM"
              "Quantum BioPharma Ltd. - Ordinary Shares - Class B (Sub Voting)")
             (asset "ALT" "Altimmune Inc")
             (asset "TERN" "Terns Pharmaceuticals Inc")
             (asset "ARQT" "Arcutis Biotherapeutics Inc")
             (asset "ACLX" "Arcellx Inc")
             (asset "OLMA" "Olema Pharmaceuticals Inc")
             (asset "VTYX" "Ventyx Biosciences Inc")
             (asset "ABSI" "Absci Corp")
             (asset "AVXL" "Anavex Life Sciences Corp")
             (asset "RZLT" "Rezolute Inc")
             (asset "TIL" "Instil Bio Inc")
             (asset "NRSN" "NeuroSense Therapeutics Ltd")
             (asset "SAVA" "Cassava Sciences Inc")
             (asset "ABCL" "AbCellera Biologics Inc")
             (asset "EVO" "Evotec SE - ADR")
             (asset "SLP" "Simulations Plus Inc.")
             (asset "GHRS" "GH Research PLC")
             (asset "DXCM" "Dexcom Inc")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset
              "BFLY"
              "Butterfly Network Inc - Ordinary Shares - Class A")
             (asset "ALIT" "Alight Inc. - Ordinary Shares - Class A")
             (asset "WELL" "Welltower Inc.")
             (asset "LLY" "Lilly(Eli) & Co")
             (asset "UNH" "Unitedhealth Group Inc")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "B" "Barrick Mining Corp.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDX" "VanEck Gold Miners ETF")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SLV" "iShares Silver Trust")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "MP" "MP Materials Corporation")
             (asset "LAC" "Lithium Americas Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset
              "TECK"
              "Teck Resources Ltd - Ordinary Shares - Class B (Sub Voting)")
             (asset "UAMY" "United States Antimony Corp")
             (asset "CPER" "United States Copper Index")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "VMC" "Vulcan Materials Co")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "SOFI" "SoFi Technologies Inc")
             (asset "AFRM" "Affirm Holdings Inc")
             (asset "UPST" "Upstart Holdings Inc")
             (asset "NU" "Nu Holdings Ltd")
             (asset "OPEN" "Opendoor Technologies Inc")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset
              "GRAB"
              "Grab Holdings Limited - Ordinary Shares - Class A")
             (asset
              "DKNG"
              "DraftKings Inc. - Ordinary Shares - Class A")
             (asset "BABA" "Alibaba Group Holding Ltd")
             (asset "PDD" "PDD Holdings Inc - ADR")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset
              "JCI"
              "Johnson Controls International plc - Registered Shares")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset
              "LPTH"
              "Lightpath Technologies, Inc. - Ordinary Shares - Class A")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset
              "PSTL"
              "Postal Realty Trust Inc - Ordinary Shares - Class A")
             (asset "CAVA" "Cava Group Inc")
             (asset
              "SMH"
              "VanEck ETF Trust - VanEck Semiconductor ETF")
             (asset
              "XLK"
              "SSgA Active Trust - State Street Technology Select Sector SPDR ETF")
             (asset
              "XLI"
              "SSgA Active Trust - State Street Industrial Select Sector SPDR ETF")
             (asset
              "XME"
              "SPDR Series Trust - State Street SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BKKT"
              "Bakkt Holdings Inc. - Ordinary Shares - Class A")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "EVTL" "Vertical Aerospace Ltd")
             (asset "QUBT" "Quantum Computing Inc")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset "BMNR" "BitMine Immersion Technologies Inc")
             (asset
              "KWEB"
              "KraneShares Trust - KraneShares CSI China Internet ETF")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "REKT"
              "Direxion Shares ETF Trust - Direxion Daily Crypto Industry Bear 1X Shares")
             (asset
              "ETH"
              "Grayscale Ethereum Staking Mini ETF - Common units of fractional undivided beneficial interest")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "SRE" "Sempra")
             (asset
              "TSLS"
              "Direxion Shares ETF Trust - Direxion Daily TSLA Bear 1X Shares")
             (asset "TSLA" "Tesla Inc")
             (asset "AAON" "AAON Inc.")
             (asset "APD" "Air Products & Chemicals Inc.")
             (asset "EQT" "EQT Corp")
             (asset "TMC" "TMC the metals company Inc")
             (asset "CSCO" "Cisco Systems, Inc.")
             (asset
              "SLVP"
              "BlackRock Institutional Trust Company N.A. - iShares MSCI Global Silver and Metals Miners ETF")])])
         (weight-equal
          [(filter
            (cumulative-return {:window 2})
            (select-top 3)
            [(asset "NVDA" "NVIDIA Corp")
             (asset "AMD" "Advanced Micro Devices Inc.")
             (asset "INTC" "Intel Corp.")
             (asset "TSM" "Taiwan Semiconductor Manufacturing - ADR")
             (asset "AVGO" "Broadcom Inc")
             (asset "MU" "Micron Technology Inc.")
             (asset "QCOM" "Qualcomm, Inc.")
             (asset "MRVL" "Marvell Technology Inc")
             (asset "ARM" "Arm Holdings plc. - ADR")
             (asset "AMAT" "Applied Materials Inc.")
             (asset "LRCX" "Lam Research Corp.")
             (asset "ALAB" "Astera Labs Inc.")
             (asset "CRDO" "Credo Technology Group")
             (asset "ON" "ON Semiconductor Corp.")
             (asset "TXN" "Texas Instruments Inc.")
             (asset "MCHP" "Microchip Technology, Inc.")
             (asset "STM" "ST Microelectronics")
             (asset "GFS" "GlobalFoundries Inc")
             (asset "DIOD" "Diodes, Inc.")
             (asset "POWI" "Power Integrations Inc.")
             (asset "SIMO" "Silicon Motion Technology Corp - ADR")
             (asset "POET" "POET Technologies Inc")
             (asset "SKYT" "SkyWater Technology Inc")
             (asset "CAMT" "Camtek Ltd")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "IONQ" "IonQ Inc")
             (asset "RGTI" "Rigetti Computing Inc")
             (asset "QBTS" "D-Wave Quantum Inc")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "PLTR" "Palantir Technologies Inc")
             (asset "APP" "Applovin Corp")
             (asset "SOUN" "SoundHound AI Inc")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "INOD" "Innodata Inc")
             (asset "TEM" "Tempus AI Inc.")
             (asset
              "QSI"
              "Quantum-Si Incorporated - Ordinary Shares - Class A")
             (asset "NBIS" "Nebius Group N.V.")
             (asset "CRM" "Salesforce Inc")
             (asset "SNOW" "Snowflake Inc")
             (asset "DDOG" "Datadog Inc - Ordinary Shares - Class A")
             (asset "MDB" "MongoDB Inc - Ordinary Shares - Class A")
             (asset "PATH" "UiPath Inc - Ordinary Shares - Class A")
             (asset "CFLT" "Confluent Inc - Ordinary Shares Class A")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "RDDT" "Reddit Inc. - Ordinary Shares - Class A")
             (asset "DUOL" "Duolingo Inc - Ordinary Shares - Class A")
             (asset "NOW" "ServiceNow Inc")
             (asset "PYPL" "PayPal Holdings Inc")
             (asset "AMPL" "Amplitude Inc - Ordinary Shares - Class A")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ORCL" "Oracle Corp.")
             (asset
              "CRWD"
              "Crowdstrike Holdings Inc - Ordinary Shares - Class A")
             (asset "PANW" "Palo Alto Networks Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc - Ordinary Shares - Class A")
             (asset "FTNT" "Fortinet Inc")
             (asset "NET" "Cloudflare Inc - Ordinary Shares - Class A")
             (asset "MSFT" "Microsoft Corporation")
             (asset "AAPL" "Apple Inc")
             (asset "GOOGL" "Alphabet Inc - Ordinary Shares - Class A")
             (asset "AMZN" "Amazon.com Inc.")
             (asset
              "META"
              "Meta Platforms Inc - Ordinary Shares - Class A")
             (asset "IBM" "International Business Machines Corp.")
             (asset "SMCI" "Super Micro Computer Inc")
             (asset "VRT" "Vertiv Holdings")
             (asset "CLS" "Celestica Inc")
             (asset "APH" "Amphenol Corp")
             (asset
              "DELL"
              "Dell Technologies Inc - Ordinary Shares - Class C")
             (asset "HPE" "Hewlett Packard Enterprise Co")
             (asset "ANET" "Arista Networks Inc")
             (asset "EQIX" "Equinix Inc")
             (asset "DLR" "Digital Realty Trust Inc")
             (asset "IRM" "Iron Mountain Inc.")
             (asset "ETN" "Eaton Corp PLC")
             (asset "HUBB" "Hubbell Inc")
             (asset "FLEX" "Flex Ltd")
             (asset "NVT" "nVent Electric PLC")
             (asset "LUMN" "Lumen Technologies Inc")
             (asset "SANM" "Sanmina Corp")
             (asset "FN" "Fabrinet")
             (asset "POWL" "Powell Industries, Inc.")
             (asset "STX" "Seagate Technology Holdings")
             (asset "WDC" "Western Digital Corp.")
             (asset "MSTR" "Strategy Inc. (MicroStrategy)")
             (asset "COIN" "Coinbase Global Inc")
             (asset "HOOD" "Robinhood Markets Inc")
             (asset "XYZ" "Block Inc")
             (asset "GLXY" "Galaxy Digital Inc.")
             (asset "MARA" "MARA Holdings Inc.")
             (asset "RIOT" "Riot Platforms Inc")
             (asset "CLSK" "Cleanspark Inc")
             (asset "CORZ" "Core Scientific Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "CIFR" "Cipher Mining Inc")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "WULF" "TeraWulf Inc")
             (asset "IREN" "IREN Ltd.")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "BITI"
              "ProShares Trust - ProShares Short Bitcoin ETF")
             (asset "ISRG" "Intuitive Surgical Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "RKLB" "Rocket Lab USA Inc")
             (asset "ASTS" "AST SpaceMobile Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset
              "SATL"
              "Satellogic Inc - Ordinary Shares - Class A")
             (asset
              "SIDU"
              "Sidus Space Inc - Ordinary Shares - Class A")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "JOBY" "Joby Aviation Inc")
             (asset "ACHR" "Archer Aviation Inc")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "BA" "Boeing Co.")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset
              "CACI"
              "Caci International Inc. - Registered Shares - Class A")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "KTOS" "Kratos Defense & Security")
             (asset "AVAV" "AeroVironment Inc.")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "KOPN" "Kopin Corp.")
             (asset "ITA" "iShares U.S. Aerospace & Defense ETF")
             (asset "CCJ" "Cameco Corp")
             (asset "OKLO" "Oklo Inc")
             (asset "SMR" "NuScale Power Corporation")
             (asset "NNE" "Nano Nuclear Energy Inc")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Funds - Global X Uranium ETF")
             (asset "CEG" "Constellation Energy Corporation")
             (asset "VST" "Vistra Corp")
             (asset "GEV" "GE Vernova Inc.")
             (asset "TLN" "Talen Energy Corp")
             (asset "NEE" "NextEra Energy Inc")
             (asset "NRG" "NRG Energy Inc.")
             (asset "AES" "AES Corp.")
             (asset "ETR" "Entergy Corp.")
             (asset "IDA" "Idacorp, Inc.")
             (asset "DUK" "Duke Energy Corp.")
             (asset "SO" "Southern Company")
             (asset "PNW" "Pinnacle West Capital Corp.")
             (asset "D" "Dominion Energy Inc")
             (asset "WMB" "Williams Cos Inc")
             (asset
              "KMI"
              "Kinder Morgan Inc - Ordinary Shares - Class P")
             (asset "ET" "Energy Transfer LP - Unit")
             (asset "CMI" "Cummins Inc")
             (asset "PWR" "Quanta Services, Inc.")
             (asset "EME" "Emcor Group, Inc.")
             (asset "MTZ" "Mastec Inc.")
             (asset "DY" "Dycom Industries, Inc.")
             (asset "MYRG" "MYR Group Inc")
             (asset "FLR" "Fluor Corporation")
             (asset "TTEK" "Tetra Tech, Inc.")
             (asset "AGX" "Argan Inc")
             (asset "STRL" "Sterling Infrastructure Inc")
             (asset "FIX" "Comfort Systems USA, Inc.")
             (asset "APG" "APi Group Corporation")
             (asset "ENPH" "Enphase Energy Inc")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset
              "CWEN"
              "Clearway Energy Inc - Ordinary Shares - Class C")
             (asset "AMRC" "Ameresco Inc. - Ordinary Shares - Class A")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "BE" "Bloom Energy Corp")
             (asset "GEVO" "Gevo Inc")
             (asset "QS" "QuantumScape Corp")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset
              "RIVN"
              "Rivian Automotive Inc - Ordinary Shares - Class A")
             (asset
              "HYLN"
              "Hyliion Holdings Corporation - Ordinary Shares - Class A")
             (asset "XOM" "Exxon Mobil Corp.")
             (asset "CVX" "Chevron Corp.")
             (asset "OXY" "Occidental Petroleum Corp.")
             (asset "DVN" "Devon Energy Corp.")
             (asset "EOG" "EOG Resources, Inc.")
             (asset "COP" "Conoco Phillips")
             (asset
              "HESM"
              "Hess Midstream LP - Ordinary Shares - Class A")
             (asset "MPC" "Marathon Petroleum Corp")
             (asset "VLO" "Valero Energy Corp.")
             (asset "PSX" "Phillips 66")
             (asset "SLB" "SLB Ltd.")
             (asset "HAL" "Halliburton Co.")
             (asset "BTU" "Peabody Energy Corp. - Ordinary Shares New")
             (asset "PBF" "PBF Energy Inc - Ordinary Shares - Class A")
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset
              "DNA"
              "Ginkgo Bioworks Holdings Inc - Ordinary Shares - Class A")
             (asset "ARCT" "Arcturus Therapeutics Holdings Inc")
             (asset "CRBU" "Caribou Biosciences Inc")
             (asset "WVE" "Wave Life Sciences Ltd.")
             (asset "RXRX" "Recursion Pharmaceuticals Inc")
             (asset "ALNY" "Alnylam Pharmaceuticals Inc")
             (asset "IONS" "Ionis Pharmaceuticals Inc")
             (asset "SRPT" "Sarepta Therapeutics Inc")
             (asset "RNA" "Avidity Biosciences Inc")
             (asset "QURE" "uniQure N.V.")
             (asset "RLAY" "Relay Therapeutics Inc")
             (asset "SLDB" "Solid Biosciences Inc")
             (asset "AUTL" "Autolus Therapeutics plc - ADR")
             (asset "VKTX" "Viking Therapeutics Inc")
             (asset "MDGL" "Madrigal Pharmaceuticals Inc")
             (asset "AXSM" "Axsome Therapeutics Inc")
             (asset "PCVX" "Vaxcyte Inc")
             (asset "CYTK" "Cytokinetics Inc")
             (asset "CRNX" "Crinetics Pharmaceuticals Inc")
             (asset "DVAX" "Dynavax Technologies Corp.")
             (asset "FATE" "Fate Therapeutics Inc")
             (asset "PRAX" "Praxis Precision Medicines Inc")
             (asset "KROS" "Keros Therapeutics Inc")
             (asset "IMNM" "Immunome Inc")
             (asset "PLRX" "Pliant Therapeutics Inc")
             (asset "MIRM" "Mirum Pharmaceuticals Inc")
             (asset "CNTA" "Centessa Pharmaceuticals plc - ADR")
             (asset "XERS" "Xeris Biopharma Holdings Inc")
             (asset "ZYME" "Zymeworks BC Inc")
             (asset "RAPT" "RAPT Therapeutics Inc")
             (asset "CELC" "Celcuity Inc")
             (asset "ABVX" "Abivax - ADR")
             (asset "MNMD" "Mind Medicine Inc")
             (asset "XFOR" "X4 Pharmaceuticals Inc")
             (asset "PLSE" "Pulse Biosciences Inc")
             (asset "CGEM" "Cullinan Therapeutics Inc")
             (asset
              "QNTM"
              "Quantum BioPharma Ltd. - Ordinary Shares - Class B (Sub Voting)")
             (asset "ALT" "Altimmune Inc")
             (asset "TERN" "Terns Pharmaceuticals Inc")
             (asset "ARQT" "Arcutis Biotherapeutics Inc")
             (asset "ACLX" "Arcellx Inc")
             (asset "OLMA" "Olema Pharmaceuticals Inc")
             (asset "VTYX" "Ventyx Biosciences Inc")
             (asset "ABSI" "Absci Corp")
             (asset "AVXL" "Anavex Life Sciences Corp")
             (asset "RZLT" "Rezolute Inc")
             (asset "TIL" "Instil Bio Inc")
             (asset "NRSN" "NeuroSense Therapeutics Ltd")
             (asset "SAVA" "Cassava Sciences Inc")
             (asset "ABCL" "AbCellera Biologics Inc")
             (asset "EVO" "Evotec SE - ADR")
             (asset "SLP" "Simulations Plus Inc.")
             (asset "GHRS" "GH Research PLC")
             (asset "DXCM" "Dexcom Inc")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset
              "BFLY"
              "Butterfly Network Inc - Ordinary Shares - Class A")
             (asset "ALIT" "Alight Inc. - Ordinary Shares - Class A")
             (asset "WELL" "Welltower Inc.")
             (asset "LLY" "Lilly(Eli) & Co")
             (asset "UNH" "Unitedhealth Group Inc")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "B" "Barrick Mining Corp.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDX" "VanEck Gold Miners ETF")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SLV" "iShares Silver Trust")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "MP" "MP Materials Corporation")
             (asset "LAC" "Lithium Americas Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset
              "TECK"
              "Teck Resources Ltd - Ordinary Shares - Class B (Sub Voting)")
             (asset "UAMY" "United States Antimony Corp")
             (asset "CPER" "United States Copper Index")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "VMC" "Vulcan Materials Co")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "SOFI" "SoFi Technologies Inc")
             (asset "AFRM" "Affirm Holdings Inc")
             (asset "UPST" "Upstart Holdings Inc")
             (asset "NU" "Nu Holdings Ltd")
             (asset "OPEN" "Opendoor Technologies Inc")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset
              "GRAB"
              "Grab Holdings Limited - Ordinary Shares - Class A")
             (asset
              "DKNG"
              "DraftKings Inc. - Ordinary Shares - Class A")
             (asset "BABA" "Alibaba Group Holding Ltd")
             (asset "PDD" "PDD Holdings Inc - ADR")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset
              "JCI"
              "Johnson Controls International plc - Registered Shares")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset
              "LPTH"
              "Lightpath Technologies, Inc. - Ordinary Shares - Class A")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset
              "PSTL"
              "Postal Realty Trust Inc - Ordinary Shares - Class A")
             (asset "CAVA" "Cava Group Inc")
             (asset
              "SMH"
              "VanEck ETF Trust - VanEck Semiconductor ETF")
             (asset
              "XLK"
              "SSgA Active Trust - State Street Technology Select Sector SPDR ETF")
             (asset
              "XLI"
              "SSgA Active Trust - State Street Industrial Select Sector SPDR ETF")
             (asset
              "XME"
              "SPDR Series Trust - State Street SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BKKT"
              "Bakkt Holdings Inc. - Ordinary Shares - Class A")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "EVTL" "Vertical Aerospace Ltd")
             (asset "QUBT" "Quantum Computing Inc")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset "BMNR" "BitMine Immersion Technologies Inc")
             (asset
              "KWEB"
              "KraneShares Trust - KraneShares CSI China Internet ETF")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "REKT"
              "Direxion Shares ETF Trust - Direxion Daily Crypto Industry Bear 1X Shares")
             (asset
              "ETH"
              "Grayscale Ethereum Staking Mini ETF - Common units of fractional undivided beneficial interest")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "SRE" "Sempra")
             (asset
              "TSLS"
              "Direxion Shares ETF Trust - Direxion Daily TSLA Bear 1X Shares")
             (asset "TSLA" "Tesla Inc")
             (asset "AAON" "AAON Inc.")
             (asset "APD" "Air Products & Chemicals Inc.")
             (asset "EQT" "EQT Corp")
             (asset "TMC" "TMC the metals company Inc")
             (asset "CSCO" "Cisco Systems, Inc.")
             (asset
              "SLVP"
              "BlackRock Institutional Trust Company N.A. - iShares MSCI Global Silver and Metals Miners ETF")])])])
       (filter
        (stdev-return {:window 7})
        (select-bottom 2)
        [(weight-equal
          [(filter
            (cumulative-return {:window 2})
            (select-top 5)
            [(asset "NVDA" "NVIDIA Corp")
             (asset "AMD" "Advanced Micro Devices Inc.")
             (asset "INTC" "Intel Corp.")
             (asset "TSM" "Taiwan Semiconductor Manufacturing - ADR")
             (asset "AVGO" "Broadcom Inc")
             (asset "MU" "Micron Technology Inc.")
             (asset "QCOM" "Qualcomm, Inc.")
             (asset "MRVL" "Marvell Technology Inc")
             (asset "ARM" "Arm Holdings plc. - ADR")
             (asset "AMAT" "Applied Materials Inc.")
             (asset "LRCX" "Lam Research Corp.")
             (asset "ALAB" "Astera Labs Inc.")
             (asset "CRDO" "Credo Technology Group")
             (asset "ON" "ON Semiconductor Corp.")
             (asset "TXN" "Texas Instruments Inc.")
             (asset "MCHP" "Microchip Technology, Inc.")
             (asset "STM" "ST Microelectronics")
             (asset "GFS" "GlobalFoundries Inc")
             (asset "DIOD" "Diodes, Inc.")
             (asset "POWI" "Power Integrations Inc.")
             (asset "SIMO" "Silicon Motion Technology Corp - ADR")
             (asset "POET" "POET Technologies Inc")
             (asset "SKYT" "SkyWater Technology Inc")
             (asset "CAMT" "Camtek Ltd")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "IONQ" "IonQ Inc")
             (asset "RGTI" "Rigetti Computing Inc")
             (asset "QBTS" "D-Wave Quantum Inc")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "PLTR" "Palantir Technologies Inc")
             (asset "APP" "Applovin Corp")
             (asset "SOUN" "SoundHound AI Inc")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "INOD" "Innodata Inc")
             (asset "TEM" "Tempus AI Inc.")
             (asset
              "QSI"
              "Quantum-Si Incorporated - Ordinary Shares - Class A")
             (asset "NBIS" "Nebius Group N.V.")
             (asset "CRM" "Salesforce Inc")
             (asset "SNOW" "Snowflake Inc")
             (asset "DDOG" "Datadog Inc - Ordinary Shares - Class A")
             (asset "MDB" "MongoDB Inc - Ordinary Shares - Class A")
             (asset "PATH" "UiPath Inc - Ordinary Shares - Class A")
             (asset "CFLT" "Confluent Inc - Ordinary Shares Class A")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "RDDT" "Reddit Inc. - Ordinary Shares - Class A")
             (asset "DUOL" "Duolingo Inc - Ordinary Shares - Class A")
             (asset "NOW" "ServiceNow Inc")
             (asset "PYPL" "PayPal Holdings Inc")
             (asset "AMPL" "Amplitude Inc - Ordinary Shares - Class A")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ORCL" "Oracle Corp.")
             (asset
              "CRWD"
              "Crowdstrike Holdings Inc - Ordinary Shares - Class A")
             (asset "PANW" "Palo Alto Networks Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc - Ordinary Shares - Class A")
             (asset "FTNT" "Fortinet Inc")
             (asset "NET" "Cloudflare Inc - Ordinary Shares - Class A")
             (asset "MSFT" "Microsoft Corporation")
             (asset "AAPL" "Apple Inc")
             (asset "GOOGL" "Alphabet Inc - Ordinary Shares - Class A")
             (asset "AMZN" "Amazon.com Inc.")
             (asset
              "META"
              "Meta Platforms Inc - Ordinary Shares - Class A")
             (asset "IBM" "International Business Machines Corp.")
             (asset "SMCI" "Super Micro Computer Inc")
             (asset "VRT" "Vertiv Holdings")
             (asset "CLS" "Celestica Inc")
             (asset "APH" "Amphenol Corp")
             (asset
              "DELL"
              "Dell Technologies Inc - Ordinary Shares - Class C")
             (asset "HPE" "Hewlett Packard Enterprise Co")
             (asset "ANET" "Arista Networks Inc")
             (asset "EQIX" "Equinix Inc")
             (asset "DLR" "Digital Realty Trust Inc")
             (asset "IRM" "Iron Mountain Inc.")
             (asset "ETN" "Eaton Corp PLC")
             (asset "HUBB" "Hubbell Inc")
             (asset "FLEX" "Flex Ltd")
             (asset "NVT" "nVent Electric PLC")
             (asset "LUMN" "Lumen Technologies Inc")
             (asset "SANM" "Sanmina Corp")
             (asset "FN" "Fabrinet")
             (asset "POWL" "Powell Industries, Inc.")
             (asset "STX" "Seagate Technology Holdings")
             (asset "WDC" "Western Digital Corp.")
             (asset "MSTR" "Strategy Inc. (MicroStrategy)")
             (asset "COIN" "Coinbase Global Inc")
             (asset "HOOD" "Robinhood Markets Inc")
             (asset "XYZ" "Block Inc")
             (asset "GLXY" "Galaxy Digital Inc.")
             (asset "MARA" "MARA Holdings Inc.")
             (asset "RIOT" "Riot Platforms Inc")
             (asset "CLSK" "Cleanspark Inc")
             (asset "CORZ" "Core Scientific Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "CIFR" "Cipher Mining Inc")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "WULF" "TeraWulf Inc")
             (asset "IREN" "IREN Ltd.")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "BITI"
              "ProShares Trust - ProShares Short Bitcoin ETF")
             (asset "ISRG" "Intuitive Surgical Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "RKLB" "Rocket Lab USA Inc")
             (asset "ASTS" "AST SpaceMobile Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset
              "SATL"
              "Satellogic Inc - Ordinary Shares - Class A")
             (asset
              "SIDU"
              "Sidus Space Inc - Ordinary Shares - Class A")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "JOBY" "Joby Aviation Inc")
             (asset "ACHR" "Archer Aviation Inc")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "BA" "Boeing Co.")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset
              "CACI"
              "Caci International Inc. - Registered Shares - Class A")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "KTOS" "Kratos Defense & Security")
             (asset "AVAV" "AeroVironment Inc.")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "KOPN" "Kopin Corp.")
             (asset "ITA" "iShares U.S. Aerospace & Defense ETF")
             (asset "CCJ" "Cameco Corp")
             (asset "OKLO" "Oklo Inc")
             (asset "SMR" "NuScale Power Corporation")
             (asset "NNE" "Nano Nuclear Energy Inc")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Funds - Global X Uranium ETF")
             (asset "CEG" "Constellation Energy Corporation")
             (asset "VST" "Vistra Corp")
             (asset "GEV" "GE Vernova Inc.")
             (asset "TLN" "Talen Energy Corp")
             (asset "NEE" "NextEra Energy Inc")
             (asset "NRG" "NRG Energy Inc.")
             (asset "AES" "AES Corp.")
             (asset "ETR" "Entergy Corp.")
             (asset "IDA" "Idacorp, Inc.")
             (asset "DUK" "Duke Energy Corp.")
             (asset "SO" "Southern Company")
             (asset "PNW" "Pinnacle West Capital Corp.")
             (asset "D" "Dominion Energy Inc")
             (asset "WMB" "Williams Cos Inc")
             (asset
              "KMI"
              "Kinder Morgan Inc - Ordinary Shares - Class P")
             (asset "ET" "Energy Transfer LP - Unit")
             (asset "CMI" "Cummins Inc")
             (asset "PWR" "Quanta Services, Inc.")
             (asset "EME" "Emcor Group, Inc.")
             (asset "MTZ" "Mastec Inc.")
             (asset "DY" "Dycom Industries, Inc.")
             (asset "MYRG" "MYR Group Inc")
             (asset "FLR" "Fluor Corporation")
             (asset "TTEK" "Tetra Tech, Inc.")
             (asset "AGX" "Argan Inc")
             (asset "STRL" "Sterling Infrastructure Inc")
             (asset "FIX" "Comfort Systems USA, Inc.")
             (asset "APG" "APi Group Corporation")
             (asset "ENPH" "Enphase Energy Inc")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset
              "CWEN"
              "Clearway Energy Inc - Ordinary Shares - Class C")
             (asset "AMRC" "Ameresco Inc. - Ordinary Shares - Class A")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "BE" "Bloom Energy Corp")
             (asset "GEVO" "Gevo Inc")
             (asset "QS" "QuantumScape Corp")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset
              "RIVN"
              "Rivian Automotive Inc - Ordinary Shares - Class A")
             (asset
              "HYLN"
              "Hyliion Holdings Corporation - Ordinary Shares - Class A")
             (asset "XOM" "Exxon Mobil Corp.")
             (asset "CVX" "Chevron Corp.")
             (asset "OXY" "Occidental Petroleum Corp.")
             (asset "DVN" "Devon Energy Corp.")
             (asset "EOG" "EOG Resources, Inc.")
             (asset "COP" "Conoco Phillips")
             (asset
              "HESM"
              "Hess Midstream LP - Ordinary Shares - Class A")
             (asset "MPC" "Marathon Petroleum Corp")
             (asset "VLO" "Valero Energy Corp.")
             (asset "PSX" "Phillips 66")
             (asset "SLB" "SLB Ltd.")
             (asset "HAL" "Halliburton Co.")
             (asset "BTU" "Peabody Energy Corp. - Ordinary Shares New")
             (asset "PBF" "PBF Energy Inc - Ordinary Shares - Class A")
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset
              "DNA"
              "Ginkgo Bioworks Holdings Inc - Ordinary Shares - Class A")
             (asset "ARCT" "Arcturus Therapeutics Holdings Inc")
             (asset "CRBU" "Caribou Biosciences Inc")
             (asset "WVE" "Wave Life Sciences Ltd.")
             (asset "RXRX" "Recursion Pharmaceuticals Inc")
             (asset "ALNY" "Alnylam Pharmaceuticals Inc")
             (asset "IONS" "Ionis Pharmaceuticals Inc")
             (asset "SRPT" "Sarepta Therapeutics Inc")
             (asset "RNA" "Avidity Biosciences Inc")
             (asset "QURE" "uniQure N.V.")
             (asset "RLAY" "Relay Therapeutics Inc")
             (asset "SLDB" "Solid Biosciences Inc")
             (asset "AUTL" "Autolus Therapeutics plc - ADR")
             (asset "VKTX" "Viking Therapeutics Inc")
             (asset "MDGL" "Madrigal Pharmaceuticals Inc")
             (asset "AXSM" "Axsome Therapeutics Inc")
             (asset "PCVX" "Vaxcyte Inc")
             (asset "CYTK" "Cytokinetics Inc")
             (asset "CRNX" "Crinetics Pharmaceuticals Inc")
             (asset "DVAX" "Dynavax Technologies Corp.")
             (asset "FATE" "Fate Therapeutics Inc")
             (asset "PRAX" "Praxis Precision Medicines Inc")
             (asset "KROS" "Keros Therapeutics Inc")
             (asset "IMNM" "Immunome Inc")
             (asset "PLRX" "Pliant Therapeutics Inc")
             (asset "MIRM" "Mirum Pharmaceuticals Inc")
             (asset "CNTA" "Centessa Pharmaceuticals plc - ADR")
             (asset "XERS" "Xeris Biopharma Holdings Inc")
             (asset "ZYME" "Zymeworks BC Inc")
             (asset "RAPT" "RAPT Therapeutics Inc")
             (asset "CELC" "Celcuity Inc")
             (asset "ABVX" "Abivax - ADR")
             (asset "MNMD" "Mind Medicine Inc")
             (asset "XFOR" "X4 Pharmaceuticals Inc")
             (asset "PLSE" "Pulse Biosciences Inc")
             (asset "CGEM" "Cullinan Therapeutics Inc")
             (asset
              "QNTM"
              "Quantum BioPharma Ltd. - Ordinary Shares - Class B (Sub Voting)")
             (asset "ALT" "Altimmune Inc")
             (asset "TERN" "Terns Pharmaceuticals Inc")
             (asset "ARQT" "Arcutis Biotherapeutics Inc")
             (asset "ACLX" "Arcellx Inc")
             (asset "OLMA" "Olema Pharmaceuticals Inc")
             (asset "VTYX" "Ventyx Biosciences Inc")
             (asset "ABSI" "Absci Corp")
             (asset "AVXL" "Anavex Life Sciences Corp")
             (asset "RZLT" "Rezolute Inc")
             (asset "TIL" "Instil Bio Inc")
             (asset "NRSN" "NeuroSense Therapeutics Ltd")
             (asset "SAVA" "Cassava Sciences Inc")
             (asset "ABCL" "AbCellera Biologics Inc")
             (asset "EVO" "Evotec SE - ADR")
             (asset "SLP" "Simulations Plus Inc.")
             (asset "GHRS" "GH Research PLC")
             (asset "DXCM" "Dexcom Inc")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset
              "BFLY"
              "Butterfly Network Inc - Ordinary Shares - Class A")
             (asset "ALIT" "Alight Inc. - Ordinary Shares - Class A")
             (asset "WELL" "Welltower Inc.")
             (asset "LLY" "Lilly(Eli) & Co")
             (asset "UNH" "Unitedhealth Group Inc")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "B" "Barrick Mining Corp.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDX" "VanEck Gold Miners ETF")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SLV" "iShares Silver Trust")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "MP" "MP Materials Corporation")
             (asset "LAC" "Lithium Americas Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset
              "TECK"
              "Teck Resources Ltd - Ordinary Shares - Class B (Sub Voting)")
             (asset "UAMY" "United States Antimony Corp")
             (asset "CPER" "United States Copper Index")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "VMC" "Vulcan Materials Co")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "SOFI" "SoFi Technologies Inc")
             (asset "AFRM" "Affirm Holdings Inc")
             (asset "UPST" "Upstart Holdings Inc")
             (asset "NU" "Nu Holdings Ltd")
             (asset "OPEN" "Opendoor Technologies Inc")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset
              "GRAB"
              "Grab Holdings Limited - Ordinary Shares - Class A")
             (asset
              "DKNG"
              "DraftKings Inc. - Ordinary Shares - Class A")
             (asset "BABA" "Alibaba Group Holding Ltd")
             (asset "PDD" "PDD Holdings Inc - ADR")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset
              "JCI"
              "Johnson Controls International plc - Registered Shares")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset
              "LPTH"
              "Lightpath Technologies, Inc. - Ordinary Shares - Class A")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset
              "PSTL"
              "Postal Realty Trust Inc - Ordinary Shares - Class A")
             (asset "CAVA" "Cava Group Inc")
             (asset
              "SMH"
              "VanEck ETF Trust - VanEck Semiconductor ETF")
             (asset
              "XLK"
              "SSgA Active Trust - State Street Technology Select Sector SPDR ETF")
             (asset
              "XLI"
              "SSgA Active Trust - State Street Industrial Select Sector SPDR ETF")
             (asset
              "XME"
              "SPDR Series Trust - State Street SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BKKT"
              "Bakkt Holdings Inc. - Ordinary Shares - Class A")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "EVTL" "Vertical Aerospace Ltd")
             (asset "QUBT" "Quantum Computing Inc")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset "BMNR" "BitMine Immersion Technologies Inc")
             (asset
              "KWEB"
              "KraneShares Trust - KraneShares CSI China Internet ETF")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "REKT"
              "Direxion Shares ETF Trust - Direxion Daily Crypto Industry Bear 1X Shares")
             (asset
              "ETH"
              "Grayscale Ethereum Staking Mini ETF - Common units of fractional undivided beneficial interest")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "SRE" "Sempra")
             (asset
              "TSLS"
              "Direxion Shares ETF Trust - Direxion Daily TSLA Bear 1X Shares")
             (asset "TSLA" "Tesla Inc")
             (asset "AAON" "AAON Inc.")
             (asset "APD" "Air Products & Chemicals Inc.")
             (asset "EQT" "EQT Corp")
             (asset "TMC" "TMC the metals company Inc")
             (asset "CSCO" "Cisco Systems, Inc.")
             (asset
              "SLVP"
              "BlackRock Institutional Trust Company N.A. - iShares MSCI Global Silver and Metals Miners ETF")])])
         (weight-equal
          [(filter
            (stdev-return {:window 2})
            (select-top 5)
            [(asset "NVDA" "NVIDIA Corp")
             (asset "AMD" "Advanced Micro Devices Inc.")
             (asset "INTC" "Intel Corp.")
             (asset "TSM" "Taiwan Semiconductor Manufacturing - ADR")
             (asset "AVGO" "Broadcom Inc")
             (asset "MU" "Micron Technology Inc.")
             (asset "QCOM" "Qualcomm, Inc.")
             (asset "MRVL" "Marvell Technology Inc")
             (asset "ARM" "Arm Holdings plc. - ADR")
             (asset "AMAT" "Applied Materials Inc.")
             (asset "LRCX" "Lam Research Corp.")
             (asset "ALAB" "Astera Labs Inc.")
             (asset "CRDO" "Credo Technology Group")
             (asset "ON" "ON Semiconductor Corp.")
             (asset "TXN" "Texas Instruments Inc.")
             (asset "MCHP" "Microchip Technology, Inc.")
             (asset "STM" "ST Microelectronics")
             (asset "GFS" "GlobalFoundries Inc")
             (asset "DIOD" "Diodes, Inc.")
             (asset "POWI" "Power Integrations Inc.")
             (asset "SIMO" "Silicon Motion Technology Corp - ADR")
             (asset "POET" "POET Technologies Inc")
             (asset "SKYT" "SkyWater Technology Inc")
             (asset "CAMT" "Camtek Ltd")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "IONQ" "IonQ Inc")
             (asset "RGTI" "Rigetti Computing Inc")
             (asset "QBTS" "D-Wave Quantum Inc")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "PLTR" "Palantir Technologies Inc")
             (asset "APP" "Applovin Corp")
             (asset "SOUN" "SoundHound AI Inc")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "INOD" "Innodata Inc")
             (asset "TEM" "Tempus AI Inc.")
             (asset
              "QSI"
              "Quantum-Si Incorporated - Ordinary Shares - Class A")
             (asset "NBIS" "Nebius Group N.V.")
             (asset "CRM" "Salesforce Inc")
             (asset "SNOW" "Snowflake Inc")
             (asset "DDOG" "Datadog Inc - Ordinary Shares - Class A")
             (asset "MDB" "MongoDB Inc - Ordinary Shares - Class A")
             (asset "PATH" "UiPath Inc - Ordinary Shares - Class A")
             (asset "CFLT" "Confluent Inc - Ordinary Shares Class A")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "RDDT" "Reddit Inc. - Ordinary Shares - Class A")
             (asset "DUOL" "Duolingo Inc - Ordinary Shares - Class A")
             (asset "NOW" "ServiceNow Inc")
             (asset "PYPL" "PayPal Holdings Inc")
             (asset "AMPL" "Amplitude Inc - Ordinary Shares - Class A")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ORCL" "Oracle Corp.")
             (asset
              "CRWD"
              "Crowdstrike Holdings Inc - Ordinary Shares - Class A")
             (asset "PANW" "Palo Alto Networks Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc - Ordinary Shares - Class A")
             (asset "FTNT" "Fortinet Inc")
             (asset "NET" "Cloudflare Inc - Ordinary Shares - Class A")
             (asset "MSFT" "Microsoft Corporation")
             (asset "AAPL" "Apple Inc")
             (asset "GOOGL" "Alphabet Inc - Ordinary Shares - Class A")
             (asset "AMZN" "Amazon.com Inc.")
             (asset
              "META"
              "Meta Platforms Inc - Ordinary Shares - Class A")
             (asset "IBM" "International Business Machines Corp.")
             (asset "SMCI" "Super Micro Computer Inc")
             (asset "VRT" "Vertiv Holdings")
             (asset "CLS" "Celestica Inc")
             (asset "APH" "Amphenol Corp")
             (asset
              "DELL"
              "Dell Technologies Inc - Ordinary Shares - Class C")
             (asset "HPE" "Hewlett Packard Enterprise Co")
             (asset "ANET" "Arista Networks Inc")
             (asset "EQIX" "Equinix Inc")
             (asset "DLR" "Digital Realty Trust Inc")
             (asset "IRM" "Iron Mountain Inc.")
             (asset "ETN" "Eaton Corp PLC")
             (asset "HUBB" "Hubbell Inc")
             (asset "FLEX" "Flex Ltd")
             (asset "NVT" "nVent Electric PLC")
             (asset "LUMN" "Lumen Technologies Inc")
             (asset "SANM" "Sanmina Corp")
             (asset "FN" "Fabrinet")
             (asset "POWL" "Powell Industries, Inc.")
             (asset "STX" "Seagate Technology Holdings")
             (asset "WDC" "Western Digital Corp.")
             (asset "MSTR" "Strategy Inc. (MicroStrategy)")
             (asset "COIN" "Coinbase Global Inc")
             (asset "HOOD" "Robinhood Markets Inc")
             (asset "XYZ" "Block Inc")
             (asset "GLXY" "Galaxy Digital Inc.")
             (asset "MARA" "MARA Holdings Inc.")
             (asset "RIOT" "Riot Platforms Inc")
             (asset "CLSK" "Cleanspark Inc")
             (asset "CORZ" "Core Scientific Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "CIFR" "Cipher Mining Inc")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "WULF" "TeraWulf Inc")
             (asset "IREN" "IREN Ltd.")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "BITI"
              "ProShares Trust - ProShares Short Bitcoin ETF")
             (asset "ISRG" "Intuitive Surgical Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "RKLB" "Rocket Lab USA Inc")
             (asset "ASTS" "AST SpaceMobile Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset
              "SATL"
              "Satellogic Inc - Ordinary Shares - Class A")
             (asset
              "SIDU"
              "Sidus Space Inc - Ordinary Shares - Class A")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "JOBY" "Joby Aviation Inc")
             (asset "ACHR" "Archer Aviation Inc")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "BA" "Boeing Co.")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset
              "CACI"
              "Caci International Inc. - Registered Shares - Class A")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "KTOS" "Kratos Defense & Security")
             (asset "AVAV" "AeroVironment Inc.")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "KOPN" "Kopin Corp.")
             (asset "ITA" "iShares U.S. Aerospace & Defense ETF")
             (asset "CCJ" "Cameco Corp")
             (asset "OKLO" "Oklo Inc")
             (asset "SMR" "NuScale Power Corporation")
             (asset "NNE" "Nano Nuclear Energy Inc")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Funds - Global X Uranium ETF")
             (asset "CEG" "Constellation Energy Corporation")
             (asset "VST" "Vistra Corp")
             (asset "GEV" "GE Vernova Inc.")
             (asset "TLN" "Talen Energy Corp")
             (asset "NEE" "NextEra Energy Inc")
             (asset "NRG" "NRG Energy Inc.")
             (asset "AES" "AES Corp.")
             (asset "ETR" "Entergy Corp.")
             (asset "IDA" "Idacorp, Inc.")
             (asset "DUK" "Duke Energy Corp.")
             (asset "SO" "Southern Company")
             (asset "PNW" "Pinnacle West Capital Corp.")
             (asset "D" "Dominion Energy Inc")
             (asset "WMB" "Williams Cos Inc")
             (asset
              "KMI"
              "Kinder Morgan Inc - Ordinary Shares - Class P")
             (asset "ET" "Energy Transfer LP - Unit")
             (asset "CMI" "Cummins Inc")
             (asset "PWR" "Quanta Services, Inc.")
             (asset "EME" "Emcor Group, Inc.")
             (asset "MTZ" "Mastec Inc.")
             (asset "DY" "Dycom Industries, Inc.")
             (asset "MYRG" "MYR Group Inc")
             (asset "FLR" "Fluor Corporation")
             (asset "TTEK" "Tetra Tech, Inc.")
             (asset "AGX" "Argan Inc")
             (asset "STRL" "Sterling Infrastructure Inc")
             (asset "FIX" "Comfort Systems USA, Inc.")
             (asset "APG" "APi Group Corporation")
             (asset "ENPH" "Enphase Energy Inc")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset
              "CWEN"
              "Clearway Energy Inc - Ordinary Shares - Class C")
             (asset "AMRC" "Ameresco Inc. - Ordinary Shares - Class A")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "BE" "Bloom Energy Corp")
             (asset "GEVO" "Gevo Inc")
             (asset "QS" "QuantumScape Corp")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset
              "RIVN"
              "Rivian Automotive Inc - Ordinary Shares - Class A")
             (asset
              "HYLN"
              "Hyliion Holdings Corporation - Ordinary Shares - Class A")
             (asset "XOM" "Exxon Mobil Corp.")
             (asset "CVX" "Chevron Corp.")
             (asset "OXY" "Occidental Petroleum Corp.")
             (asset "DVN" "Devon Energy Corp.")
             (asset "EOG" "EOG Resources, Inc.")
             (asset "COP" "Conoco Phillips")
             (asset
              "HESM"
              "Hess Midstream LP - Ordinary Shares - Class A")
             (asset "MPC" "Marathon Petroleum Corp")
             (asset "VLO" "Valero Energy Corp.")
             (asset "PSX" "Phillips 66")
             (asset "SLB" "SLB Ltd.")
             (asset "HAL" "Halliburton Co.")
             (asset "BTU" "Peabody Energy Corp. - Ordinary Shares New")
             (asset "PBF" "PBF Energy Inc - Ordinary Shares - Class A")
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset
              "DNA"
              "Ginkgo Bioworks Holdings Inc - Ordinary Shares - Class A")
             (asset "ARCT" "Arcturus Therapeutics Holdings Inc")
             (asset "CRBU" "Caribou Biosciences Inc")
             (asset "WVE" "Wave Life Sciences Ltd.")
             (asset "RXRX" "Recursion Pharmaceuticals Inc")
             (asset "ALNY" "Alnylam Pharmaceuticals Inc")
             (asset "IONS" "Ionis Pharmaceuticals Inc")
             (asset "SRPT" "Sarepta Therapeutics Inc")
             (asset "RNA" "Avidity Biosciences Inc")
             (asset "QURE" "uniQure N.V.")
             (asset "RLAY" "Relay Therapeutics Inc")
             (asset "SLDB" "Solid Biosciences Inc")
             (asset "AUTL" "Autolus Therapeutics plc - ADR")
             (asset "VKTX" "Viking Therapeutics Inc")
             (asset "MDGL" "Madrigal Pharmaceuticals Inc")
             (asset "AXSM" "Axsome Therapeutics Inc")
             (asset "PCVX" "Vaxcyte Inc")
             (asset "CYTK" "Cytokinetics Inc")
             (asset "CRNX" "Crinetics Pharmaceuticals Inc")
             (asset "DVAX" "Dynavax Technologies Corp.")
             (asset "FATE" "Fate Therapeutics Inc")
             (asset "PRAX" "Praxis Precision Medicines Inc")
             (asset "KROS" "Keros Therapeutics Inc")
             (asset "IMNM" "Immunome Inc")
             (asset "PLRX" "Pliant Therapeutics Inc")
             (asset "MIRM" "Mirum Pharmaceuticals Inc")
             (asset "CNTA" "Centessa Pharmaceuticals plc - ADR")
             (asset "XERS" "Xeris Biopharma Holdings Inc")
             (asset "ZYME" "Zymeworks BC Inc")
             (asset "RAPT" "RAPT Therapeutics Inc")
             (asset "CELC" "Celcuity Inc")
             (asset "ABVX" "Abivax - ADR")
             (asset "MNMD" "Mind Medicine Inc")
             (asset "XFOR" "X4 Pharmaceuticals Inc")
             (asset "PLSE" "Pulse Biosciences Inc")
             (asset "CGEM" "Cullinan Therapeutics Inc")
             (asset
              "QNTM"
              "Quantum BioPharma Ltd. - Ordinary Shares - Class B (Sub Voting)")
             (asset "ALT" "Altimmune Inc")
             (asset "TERN" "Terns Pharmaceuticals Inc")
             (asset "ARQT" "Arcutis Biotherapeutics Inc")
             (asset "ACLX" "Arcellx Inc")
             (asset "OLMA" "Olema Pharmaceuticals Inc")
             (asset "VTYX" "Ventyx Biosciences Inc")
             (asset "ABSI" "Absci Corp")
             (asset "AVXL" "Anavex Life Sciences Corp")
             (asset "RZLT" "Rezolute Inc")
             (asset "TIL" "Instil Bio Inc")
             (asset "NRSN" "NeuroSense Therapeutics Ltd")
             (asset "SAVA" "Cassava Sciences Inc")
             (asset "ABCL" "AbCellera Biologics Inc")
             (asset "EVO" "Evotec SE - ADR")
             (asset "SLP" "Simulations Plus Inc.")
             (asset "GHRS" "GH Research PLC")
             (asset "DXCM" "Dexcom Inc")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset
              "BFLY"
              "Butterfly Network Inc - Ordinary Shares - Class A")
             (asset "ALIT" "Alight Inc. - Ordinary Shares - Class A")
             (asset "WELL" "Welltower Inc.")
             (asset "LLY" "Lilly(Eli) & Co")
             (asset "UNH" "Unitedhealth Group Inc")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "B" "Barrick Mining Corp.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDX" "VanEck Gold Miners ETF")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SLV" "iShares Silver Trust")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "MP" "MP Materials Corporation")
             (asset "LAC" "Lithium Americas Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset
              "TECK"
              "Teck Resources Ltd - Ordinary Shares - Class B (Sub Voting)")
             (asset "UAMY" "United States Antimony Corp")
             (asset "CPER" "United States Copper Index")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "VMC" "Vulcan Materials Co")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "SOFI" "SoFi Technologies Inc")
             (asset "AFRM" "Affirm Holdings Inc")
             (asset "UPST" "Upstart Holdings Inc")
             (asset "NU" "Nu Holdings Ltd")
             (asset "OPEN" "Opendoor Technologies Inc")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset
              "GRAB"
              "Grab Holdings Limited - Ordinary Shares - Class A")
             (asset
              "DKNG"
              "DraftKings Inc. - Ordinary Shares - Class A")
             (asset "BABA" "Alibaba Group Holding Ltd")
             (asset "PDD" "PDD Holdings Inc - ADR")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset
              "JCI"
              "Johnson Controls International plc - Registered Shares")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset
              "LPTH"
              "Lightpath Technologies, Inc. - Ordinary Shares - Class A")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset
              "PSTL"
              "Postal Realty Trust Inc - Ordinary Shares - Class A")
             (asset "CAVA" "Cava Group Inc")
             (asset
              "SMH"
              "VanEck ETF Trust - VanEck Semiconductor ETF")
             (asset
              "XLK"
              "SSgA Active Trust - State Street Technology Select Sector SPDR ETF")
             (asset
              "XLI"
              "SSgA Active Trust - State Street Industrial Select Sector SPDR ETF")
             (asset
              "XME"
              "SPDR Series Trust - State Street SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BKKT"
              "Bakkt Holdings Inc. - Ordinary Shares - Class A")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "EVTL" "Vertical Aerospace Ltd")
             (asset "QUBT" "Quantum Computing Inc")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset "BMNR" "BitMine Immersion Technologies Inc")
             (asset
              "KWEB"
              "KraneShares Trust - KraneShares CSI China Internet ETF")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "REKT"
              "Direxion Shares ETF Trust - Direxion Daily Crypto Industry Bear 1X Shares")
             (asset
              "ETH"
              "Grayscale Ethereum Staking Mini ETF - Common units of fractional undivided beneficial interest")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "SRE" "Sempra")
             (asset
              "TSLS"
              "Direxion Shares ETF Trust - Direxion Daily TSLA Bear 1X Shares")
             (asset "TSLA" "Tesla Inc")
             (asset "AAON" "AAON Inc.")
             (asset "APD" "Air Products & Chemicals Inc.")
             (asset "EQT" "EQT Corp")
             (asset "TMC" "TMC the metals company Inc")
             (asset "CSCO" "Cisco Systems, Inc.")
             (asset
              "SLVP"
              "BlackRock Institutional Trust Company N.A. - iShares MSCI Global Silver and Metals Miners ETF")])])
         (weight-equal
          [(filter
            (stdev-return {:window 2})
            (select-top 3)
            [(asset "NVDA" "NVIDIA Corp")
             (asset "AMD" "Advanced Micro Devices Inc.")
             (asset "INTC" "Intel Corp.")
             (asset "TSM" "Taiwan Semiconductor Manufacturing - ADR")
             (asset "AVGO" "Broadcom Inc")
             (asset "MU" "Micron Technology Inc.")
             (asset "QCOM" "Qualcomm, Inc.")
             (asset "MRVL" "Marvell Technology Inc")
             (asset "ARM" "Arm Holdings plc. - ADR")
             (asset "AMAT" "Applied Materials Inc.")
             (asset "LRCX" "Lam Research Corp.")
             (asset "ALAB" "Astera Labs Inc.")
             (asset "CRDO" "Credo Technology Group")
             (asset "ON" "ON Semiconductor Corp.")
             (asset "TXN" "Texas Instruments Inc.")
             (asset "MCHP" "Microchip Technology, Inc.")
             (asset "STM" "ST Microelectronics")
             (asset "GFS" "GlobalFoundries Inc")
             (asset "DIOD" "Diodes, Inc.")
             (asset "POWI" "Power Integrations Inc.")
             (asset "SIMO" "Silicon Motion Technology Corp - ADR")
             (asset "POET" "POET Technologies Inc")
             (asset "SKYT" "SkyWater Technology Inc")
             (asset "CAMT" "Camtek Ltd")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "IONQ" "IonQ Inc")
             (asset "RGTI" "Rigetti Computing Inc")
             (asset "QBTS" "D-Wave Quantum Inc")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "PLTR" "Palantir Technologies Inc")
             (asset "APP" "Applovin Corp")
             (asset "SOUN" "SoundHound AI Inc")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "INOD" "Innodata Inc")
             (asset "TEM" "Tempus AI Inc.")
             (asset
              "QSI"
              "Quantum-Si Incorporated - Ordinary Shares - Class A")
             (asset "NBIS" "Nebius Group N.V.")
             (asset "CRM" "Salesforce Inc")
             (asset "SNOW" "Snowflake Inc")
             (asset "DDOG" "Datadog Inc - Ordinary Shares - Class A")
             (asset "MDB" "MongoDB Inc - Ordinary Shares - Class A")
             (asset "PATH" "UiPath Inc - Ordinary Shares - Class A")
             (asset "CFLT" "Confluent Inc - Ordinary Shares Class A")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "RDDT" "Reddit Inc. - Ordinary Shares - Class A")
             (asset "DUOL" "Duolingo Inc - Ordinary Shares - Class A")
             (asset "NOW" "ServiceNow Inc")
             (asset "PYPL" "PayPal Holdings Inc")
             (asset "AMPL" "Amplitude Inc - Ordinary Shares - Class A")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ORCL" "Oracle Corp.")
             (asset
              "CRWD"
              "Crowdstrike Holdings Inc - Ordinary Shares - Class A")
             (asset "PANW" "Palo Alto Networks Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc - Ordinary Shares - Class A")
             (asset "FTNT" "Fortinet Inc")
             (asset "NET" "Cloudflare Inc - Ordinary Shares - Class A")
             (asset "MSFT" "Microsoft Corporation")
             (asset "AAPL" "Apple Inc")
             (asset "GOOGL" "Alphabet Inc - Ordinary Shares - Class A")
             (asset "AMZN" "Amazon.com Inc.")
             (asset
              "META"
              "Meta Platforms Inc - Ordinary Shares - Class A")
             (asset "IBM" "International Business Machines Corp.")
             (asset "SMCI" "Super Micro Computer Inc")
             (asset "VRT" "Vertiv Holdings")
             (asset "CLS" "Celestica Inc")
             (asset "APH" "Amphenol Corp")
             (asset
              "DELL"
              "Dell Technologies Inc - Ordinary Shares - Class C")
             (asset "HPE" "Hewlett Packard Enterprise Co")
             (asset "ANET" "Arista Networks Inc")
             (asset "EQIX" "Equinix Inc")
             (asset "DLR" "Digital Realty Trust Inc")
             (asset "IRM" "Iron Mountain Inc.")
             (asset "ETN" "Eaton Corp PLC")
             (asset "HUBB" "Hubbell Inc")
             (asset "FLEX" "Flex Ltd")
             (asset "NVT" "nVent Electric PLC")
             (asset "LUMN" "Lumen Technologies Inc")
             (asset "SANM" "Sanmina Corp")
             (asset "FN" "Fabrinet")
             (asset "POWL" "Powell Industries, Inc.")
             (asset "STX" "Seagate Technology Holdings")
             (asset "WDC" "Western Digital Corp.")
             (asset "MSTR" "Strategy Inc. (MicroStrategy)")
             (asset "COIN" "Coinbase Global Inc")
             (asset "HOOD" "Robinhood Markets Inc")
             (asset "XYZ" "Block Inc")
             (asset "GLXY" "Galaxy Digital Inc.")
             (asset "MARA" "MARA Holdings Inc.")
             (asset "RIOT" "Riot Platforms Inc")
             (asset "CLSK" "Cleanspark Inc")
             (asset "CORZ" "Core Scientific Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "CIFR" "Cipher Mining Inc")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "WULF" "TeraWulf Inc")
             (asset "IREN" "IREN Ltd.")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "BITI"
              "ProShares Trust - ProShares Short Bitcoin ETF")
             (asset "ISRG" "Intuitive Surgical Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "RKLB" "Rocket Lab USA Inc")
             (asset "ASTS" "AST SpaceMobile Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset
              "SATL"
              "Satellogic Inc - Ordinary Shares - Class A")
             (asset
              "SIDU"
              "Sidus Space Inc - Ordinary Shares - Class A")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "JOBY" "Joby Aviation Inc")
             (asset "ACHR" "Archer Aviation Inc")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "BA" "Boeing Co.")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset
              "CACI"
              "Caci International Inc. - Registered Shares - Class A")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "KTOS" "Kratos Defense & Security")
             (asset "AVAV" "AeroVironment Inc.")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "KOPN" "Kopin Corp.")
             (asset "ITA" "iShares U.S. Aerospace & Defense ETF")
             (asset "CCJ" "Cameco Corp")
             (asset "OKLO" "Oklo Inc")
             (asset "SMR" "NuScale Power Corporation")
             (asset "NNE" "Nano Nuclear Energy Inc")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Funds - Global X Uranium ETF")
             (asset "CEG" "Constellation Energy Corporation")
             (asset "VST" "Vistra Corp")
             (asset "GEV" "GE Vernova Inc.")
             (asset "TLN" "Talen Energy Corp")
             (asset "NEE" "NextEra Energy Inc")
             (asset "NRG" "NRG Energy Inc.")
             (asset "AES" "AES Corp.")
             (asset "ETR" "Entergy Corp.")
             (asset "IDA" "Idacorp, Inc.")
             (asset "DUK" "Duke Energy Corp.")
             (asset "SO" "Southern Company")
             (asset "PNW" "Pinnacle West Capital Corp.")
             (asset "D" "Dominion Energy Inc")
             (asset "WMB" "Williams Cos Inc")
             (asset
              "KMI"
              "Kinder Morgan Inc - Ordinary Shares - Class P")
             (asset "ET" "Energy Transfer LP - Unit")
             (asset "CMI" "Cummins Inc")
             (asset "PWR" "Quanta Services, Inc.")
             (asset "EME" "Emcor Group, Inc.")
             (asset "MTZ" "Mastec Inc.")
             (asset "DY" "Dycom Industries, Inc.")
             (asset "MYRG" "MYR Group Inc")
             (asset "FLR" "Fluor Corporation")
             (asset "TTEK" "Tetra Tech, Inc.")
             (asset "AGX" "Argan Inc")
             (asset "STRL" "Sterling Infrastructure Inc")
             (asset "FIX" "Comfort Systems USA, Inc.")
             (asset "APG" "APi Group Corporation")
             (asset "ENPH" "Enphase Energy Inc")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset
              "CWEN"
              "Clearway Energy Inc - Ordinary Shares - Class C")
             (asset "AMRC" "Ameresco Inc. - Ordinary Shares - Class A")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "BE" "Bloom Energy Corp")
             (asset "GEVO" "Gevo Inc")
             (asset "QS" "QuantumScape Corp")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset
              "RIVN"
              "Rivian Automotive Inc - Ordinary Shares - Class A")
             (asset
              "HYLN"
              "Hyliion Holdings Corporation - Ordinary Shares - Class A")
             (asset "XOM" "Exxon Mobil Corp.")
             (asset "CVX" "Chevron Corp.")
             (asset "OXY" "Occidental Petroleum Corp.")
             (asset "DVN" "Devon Energy Corp.")
             (asset "EOG" "EOG Resources, Inc.")
             (asset "COP" "Conoco Phillips")
             (asset
              "HESM"
              "Hess Midstream LP - Ordinary Shares - Class A")
             (asset "MPC" "Marathon Petroleum Corp")
             (asset "VLO" "Valero Energy Corp.")
             (asset "PSX" "Phillips 66")
             (asset "SLB" "SLB Ltd.")
             (asset "HAL" "Halliburton Co.")
             (asset "BTU" "Peabody Energy Corp. - Ordinary Shares New")
             (asset "PBF" "PBF Energy Inc - Ordinary Shares - Class A")
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset
              "DNA"
              "Ginkgo Bioworks Holdings Inc - Ordinary Shares - Class A")
             (asset "ARCT" "Arcturus Therapeutics Holdings Inc")
             (asset "CRBU" "Caribou Biosciences Inc")
             (asset "WVE" "Wave Life Sciences Ltd.")
             (asset "RXRX" "Recursion Pharmaceuticals Inc")
             (asset "ALNY" "Alnylam Pharmaceuticals Inc")
             (asset "IONS" "Ionis Pharmaceuticals Inc")
             (asset "SRPT" "Sarepta Therapeutics Inc")
             (asset "RNA" "Avidity Biosciences Inc")
             (asset "QURE" "uniQure N.V.")
             (asset "RLAY" "Relay Therapeutics Inc")
             (asset "SLDB" "Solid Biosciences Inc")
             (asset "AUTL" "Autolus Therapeutics plc - ADR")
             (asset "VKTX" "Viking Therapeutics Inc")
             (asset "MDGL" "Madrigal Pharmaceuticals Inc")
             (asset "AXSM" "Axsome Therapeutics Inc")
             (asset "PCVX" "Vaxcyte Inc")
             (asset "CYTK" "Cytokinetics Inc")
             (asset "CRNX" "Crinetics Pharmaceuticals Inc")
             (asset "DVAX" "Dynavax Technologies Corp.")
             (asset "FATE" "Fate Therapeutics Inc")
             (asset "PRAX" "Praxis Precision Medicines Inc")
             (asset "KROS" "Keros Therapeutics Inc")
             (asset "IMNM" "Immunome Inc")
             (asset "PLRX" "Pliant Therapeutics Inc")
             (asset "MIRM" "Mirum Pharmaceuticals Inc")
             (asset "CNTA" "Centessa Pharmaceuticals plc - ADR")
             (asset "XERS" "Xeris Biopharma Holdings Inc")
             (asset "ZYME" "Zymeworks BC Inc")
             (asset "RAPT" "RAPT Therapeutics Inc")
             (asset "CELC" "Celcuity Inc")
             (asset "ABVX" "Abivax - ADR")
             (asset "MNMD" "Mind Medicine Inc")
             (asset "XFOR" "X4 Pharmaceuticals Inc")
             (asset "PLSE" "Pulse Biosciences Inc")
             (asset "CGEM" "Cullinan Therapeutics Inc")
             (asset
              "QNTM"
              "Quantum BioPharma Ltd. - Ordinary Shares - Class B (Sub Voting)")
             (asset "ALT" "Altimmune Inc")
             (asset "TERN" "Terns Pharmaceuticals Inc")
             (asset "ARQT" "Arcutis Biotherapeutics Inc")
             (asset "ACLX" "Arcellx Inc")
             (asset "OLMA" "Olema Pharmaceuticals Inc")
             (asset "VTYX" "Ventyx Biosciences Inc")
             (asset "ABSI" "Absci Corp")
             (asset "AVXL" "Anavex Life Sciences Corp")
             (asset "RZLT" "Rezolute Inc")
             (asset "TIL" "Instil Bio Inc")
             (asset "NRSN" "NeuroSense Therapeutics Ltd")
             (asset "SAVA" "Cassava Sciences Inc")
             (asset "ABCL" "AbCellera Biologics Inc")
             (asset "EVO" "Evotec SE - ADR")
             (asset "SLP" "Simulations Plus Inc.")
             (asset "GHRS" "GH Research PLC")
             (asset "DXCM" "Dexcom Inc")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset
              "BFLY"
              "Butterfly Network Inc - Ordinary Shares - Class A")
             (asset "ALIT" "Alight Inc. - Ordinary Shares - Class A")
             (asset "WELL" "Welltower Inc.")
             (asset "LLY" "Lilly(Eli) & Co")
             (asset "UNH" "Unitedhealth Group Inc")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "B" "Barrick Mining Corp.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDX" "VanEck Gold Miners ETF")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SLV" "iShares Silver Trust")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "MP" "MP Materials Corporation")
             (asset "LAC" "Lithium Americas Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset
              "TECK"
              "Teck Resources Ltd - Ordinary Shares - Class B (Sub Voting)")
             (asset "UAMY" "United States Antimony Corp")
             (asset "CPER" "United States Copper Index")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "VMC" "Vulcan Materials Co")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "SOFI" "SoFi Technologies Inc")
             (asset "AFRM" "Affirm Holdings Inc")
             (asset "UPST" "Upstart Holdings Inc")
             (asset "NU" "Nu Holdings Ltd")
             (asset "OPEN" "Opendoor Technologies Inc")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset
              "GRAB"
              "Grab Holdings Limited - Ordinary Shares - Class A")
             (asset
              "DKNG"
              "DraftKings Inc. - Ordinary Shares - Class A")
             (asset "BABA" "Alibaba Group Holding Ltd")
             (asset "PDD" "PDD Holdings Inc - ADR")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset
              "JCI"
              "Johnson Controls International plc - Registered Shares")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset
              "LPTH"
              "Lightpath Technologies, Inc. - Ordinary Shares - Class A")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset
              "PSTL"
              "Postal Realty Trust Inc - Ordinary Shares - Class A")
             (asset "CAVA" "Cava Group Inc")
             (asset
              "SMH"
              "VanEck ETF Trust - VanEck Semiconductor ETF")
             (asset
              "XLK"
              "SSgA Active Trust - State Street Technology Select Sector SPDR ETF")
             (asset
              "XLI"
              "SSgA Active Trust - State Street Industrial Select Sector SPDR ETF")
             (asset
              "XME"
              "SPDR Series Trust - State Street SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BKKT"
              "Bakkt Holdings Inc. - Ordinary Shares - Class A")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "EVTL" "Vertical Aerospace Ltd")
             (asset "QUBT" "Quantum Computing Inc")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset "BMNR" "BitMine Immersion Technologies Inc")
             (asset
              "KWEB"
              "KraneShares Trust - KraneShares CSI China Internet ETF")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "REKT"
              "Direxion Shares ETF Trust - Direxion Daily Crypto Industry Bear 1X Shares")
             (asset
              "ETH"
              "Grayscale Ethereum Staking Mini ETF - Common units of fractional undivided beneficial interest")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "SRE" "Sempra")
             (asset
              "TSLS"
              "Direxion Shares ETF Trust - Direxion Daily TSLA Bear 1X Shares")
             (asset "TSLA" "Tesla Inc")
             (asset "AAON" "AAON Inc.")
             (asset "APD" "Air Products & Chemicals Inc.")
             (asset "EQT" "EQT Corp")
             (asset "TMC" "TMC the metals company Inc")
             (asset "CSCO" "Cisco Systems, Inc.")
             (asset
              "SLVP"
              "BlackRock Institutional Trust Company N.A. - iShares MSCI Global Silver and Metals Miners ETF")])])
         (weight-equal
          [(filter
            (cumulative-return {:window 2})
            (select-top 3)
            [(asset "NVDA" "NVIDIA Corp")
             (asset "AMD" "Advanced Micro Devices Inc.")
             (asset "INTC" "Intel Corp.")
             (asset "TSM" "Taiwan Semiconductor Manufacturing - ADR")
             (asset "AVGO" "Broadcom Inc")
             (asset "MU" "Micron Technology Inc.")
             (asset "QCOM" "Qualcomm, Inc.")
             (asset "MRVL" "Marvell Technology Inc")
             (asset "ARM" "Arm Holdings plc. - ADR")
             (asset "AMAT" "Applied Materials Inc.")
             (asset "LRCX" "Lam Research Corp.")
             (asset "ALAB" "Astera Labs Inc.")
             (asset "CRDO" "Credo Technology Group")
             (asset "ON" "ON Semiconductor Corp.")
             (asset "TXN" "Texas Instruments Inc.")
             (asset "MCHP" "Microchip Technology, Inc.")
             (asset "STM" "ST Microelectronics")
             (asset "GFS" "GlobalFoundries Inc")
             (asset "DIOD" "Diodes, Inc.")
             (asset "POWI" "Power Integrations Inc.")
             (asset "SIMO" "Silicon Motion Technology Corp - ADR")
             (asset "POET" "POET Technologies Inc")
             (asset "SKYT" "SkyWater Technology Inc")
             (asset "CAMT" "Camtek Ltd")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "IONQ" "IonQ Inc")
             (asset "RGTI" "Rigetti Computing Inc")
             (asset "QBTS" "D-Wave Quantum Inc")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "PLTR" "Palantir Technologies Inc")
             (asset "APP" "Applovin Corp")
             (asset "SOUN" "SoundHound AI Inc")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "INOD" "Innodata Inc")
             (asset "TEM" "Tempus AI Inc.")
             (asset
              "QSI"
              "Quantum-Si Incorporated - Ordinary Shares - Class A")
             (asset "NBIS" "Nebius Group N.V.")
             (asset "CRM" "Salesforce Inc")
             (asset "SNOW" "Snowflake Inc")
             (asset "DDOG" "Datadog Inc - Ordinary Shares - Class A")
             (asset "MDB" "MongoDB Inc - Ordinary Shares - Class A")
             (asset "PATH" "UiPath Inc - Ordinary Shares - Class A")
             (asset "CFLT" "Confluent Inc - Ordinary Shares Class A")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "RDDT" "Reddit Inc. - Ordinary Shares - Class A")
             (asset "DUOL" "Duolingo Inc - Ordinary Shares - Class A")
             (asset "NOW" "ServiceNow Inc")
             (asset "PYPL" "PayPal Holdings Inc")
             (asset "AMPL" "Amplitude Inc - Ordinary Shares - Class A")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ORCL" "Oracle Corp.")
             (asset
              "CRWD"
              "Crowdstrike Holdings Inc - Ordinary Shares - Class A")
             (asset "PANW" "Palo Alto Networks Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc - Ordinary Shares - Class A")
             (asset "FTNT" "Fortinet Inc")
             (asset "NET" "Cloudflare Inc - Ordinary Shares - Class A")
             (asset "MSFT" "Microsoft Corporation")
             (asset "AAPL" "Apple Inc")
             (asset "GOOGL" "Alphabet Inc - Ordinary Shares - Class A")
             (asset "AMZN" "Amazon.com Inc.")
             (asset
              "META"
              "Meta Platforms Inc - Ordinary Shares - Class A")
             (asset "IBM" "International Business Machines Corp.")
             (asset "SMCI" "Super Micro Computer Inc")
             (asset "VRT" "Vertiv Holdings")
             (asset "CLS" "Celestica Inc")
             (asset "APH" "Amphenol Corp")
             (asset
              "DELL"
              "Dell Technologies Inc - Ordinary Shares - Class C")
             (asset "HPE" "Hewlett Packard Enterprise Co")
             (asset "ANET" "Arista Networks Inc")
             (asset "EQIX" "Equinix Inc")
             (asset "DLR" "Digital Realty Trust Inc")
             (asset "IRM" "Iron Mountain Inc.")
             (asset "ETN" "Eaton Corp PLC")
             (asset "HUBB" "Hubbell Inc")
             (asset "FLEX" "Flex Ltd")
             (asset "NVT" "nVent Electric PLC")
             (asset "LUMN" "Lumen Technologies Inc")
             (asset "SANM" "Sanmina Corp")
             (asset "FN" "Fabrinet")
             (asset "POWL" "Powell Industries, Inc.")
             (asset "STX" "Seagate Technology Holdings")
             (asset "WDC" "Western Digital Corp.")
             (asset "MSTR" "Strategy Inc. (MicroStrategy)")
             (asset "COIN" "Coinbase Global Inc")
             (asset "HOOD" "Robinhood Markets Inc")
             (asset "XYZ" "Block Inc")
             (asset "GLXY" "Galaxy Digital Inc.")
             (asset "MARA" "MARA Holdings Inc.")
             (asset "RIOT" "Riot Platforms Inc")
             (asset "CLSK" "Cleanspark Inc")
             (asset "CORZ" "Core Scientific Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "CIFR" "Cipher Mining Inc")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "WULF" "TeraWulf Inc")
             (asset "IREN" "IREN Ltd.")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "BITI"
              "ProShares Trust - ProShares Short Bitcoin ETF")
             (asset "ISRG" "Intuitive Surgical Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "RKLB" "Rocket Lab USA Inc")
             (asset "ASTS" "AST SpaceMobile Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset
              "SATL"
              "Satellogic Inc - Ordinary Shares - Class A")
             (asset
              "SIDU"
              "Sidus Space Inc - Ordinary Shares - Class A")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "JOBY" "Joby Aviation Inc")
             (asset "ACHR" "Archer Aviation Inc")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "BA" "Boeing Co.")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset
              "CACI"
              "Caci International Inc. - Registered Shares - Class A")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "KTOS" "Kratos Defense & Security")
             (asset "AVAV" "AeroVironment Inc.")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "KOPN" "Kopin Corp.")
             (asset "ITA" "iShares U.S. Aerospace & Defense ETF")
             (asset "CCJ" "Cameco Corp")
             (asset "OKLO" "Oklo Inc")
             (asset "SMR" "NuScale Power Corporation")
             (asset "NNE" "Nano Nuclear Energy Inc")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Funds - Global X Uranium ETF")
             (asset "CEG" "Constellation Energy Corporation")
             (asset "VST" "Vistra Corp")
             (asset "GEV" "GE Vernova Inc.")
             (asset "TLN" "Talen Energy Corp")
             (asset "NEE" "NextEra Energy Inc")
             (asset "NRG" "NRG Energy Inc.")
             (asset "AES" "AES Corp.")
             (asset "ETR" "Entergy Corp.")
             (asset "IDA" "Idacorp, Inc.")
             (asset "DUK" "Duke Energy Corp.")
             (asset "SO" "Southern Company")
             (asset "PNW" "Pinnacle West Capital Corp.")
             (asset "D" "Dominion Energy Inc")
             (asset "WMB" "Williams Cos Inc")
             (asset
              "KMI"
              "Kinder Morgan Inc - Ordinary Shares - Class P")
             (asset "ET" "Energy Transfer LP - Unit")
             (asset "CMI" "Cummins Inc")
             (asset "PWR" "Quanta Services, Inc.")
             (asset "EME" "Emcor Group, Inc.")
             (asset "MTZ" "Mastec Inc.")
             (asset "DY" "Dycom Industries, Inc.")
             (asset "MYRG" "MYR Group Inc")
             (asset "FLR" "Fluor Corporation")
             (asset "TTEK" "Tetra Tech, Inc.")
             (asset "AGX" "Argan Inc")
             (asset "STRL" "Sterling Infrastructure Inc")
             (asset "FIX" "Comfort Systems USA, Inc.")
             (asset "APG" "APi Group Corporation")
             (asset "ENPH" "Enphase Energy Inc")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset
              "CWEN"
              "Clearway Energy Inc - Ordinary Shares - Class C")
             (asset "AMRC" "Ameresco Inc. - Ordinary Shares - Class A")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "BE" "Bloom Energy Corp")
             (asset "GEVO" "Gevo Inc")
             (asset "QS" "QuantumScape Corp")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset
              "RIVN"
              "Rivian Automotive Inc - Ordinary Shares - Class A")
             (asset
              "HYLN"
              "Hyliion Holdings Corporation - Ordinary Shares - Class A")
             (asset "XOM" "Exxon Mobil Corp.")
             (asset "CVX" "Chevron Corp.")
             (asset "OXY" "Occidental Petroleum Corp.")
             (asset "DVN" "Devon Energy Corp.")
             (asset "EOG" "EOG Resources, Inc.")
             (asset "COP" "Conoco Phillips")
             (asset
              "HESM"
              "Hess Midstream LP - Ordinary Shares - Class A")
             (asset "MPC" "Marathon Petroleum Corp")
             (asset "VLO" "Valero Energy Corp.")
             (asset "PSX" "Phillips 66")
             (asset "SLB" "SLB Ltd.")
             (asset "HAL" "Halliburton Co.")
             (asset "BTU" "Peabody Energy Corp. - Ordinary Shares New")
             (asset "PBF" "PBF Energy Inc - Ordinary Shares - Class A")
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset
              "DNA"
              "Ginkgo Bioworks Holdings Inc - Ordinary Shares - Class A")
             (asset "ARCT" "Arcturus Therapeutics Holdings Inc")
             (asset "CRBU" "Caribou Biosciences Inc")
             (asset "WVE" "Wave Life Sciences Ltd.")
             (asset "RXRX" "Recursion Pharmaceuticals Inc")
             (asset "ALNY" "Alnylam Pharmaceuticals Inc")
             (asset "IONS" "Ionis Pharmaceuticals Inc")
             (asset "SRPT" "Sarepta Therapeutics Inc")
             (asset "RNA" "Avidity Biosciences Inc")
             (asset "QURE" "uniQure N.V.")
             (asset "RLAY" "Relay Therapeutics Inc")
             (asset "SLDB" "Solid Biosciences Inc")
             (asset "AUTL" "Autolus Therapeutics plc - ADR")
             (asset "VKTX" "Viking Therapeutics Inc")
             (asset "MDGL" "Madrigal Pharmaceuticals Inc")
             (asset "AXSM" "Axsome Therapeutics Inc")
             (asset "PCVX" "Vaxcyte Inc")
             (asset "CYTK" "Cytokinetics Inc")
             (asset "CRNX" "Crinetics Pharmaceuticals Inc")
             (asset "DVAX" "Dynavax Technologies Corp.")
             (asset "FATE" "Fate Therapeutics Inc")
             (asset "PRAX" "Praxis Precision Medicines Inc")
             (asset "KROS" "Keros Therapeutics Inc")
             (asset "IMNM" "Immunome Inc")
             (asset "PLRX" "Pliant Therapeutics Inc")
             (asset "MIRM" "Mirum Pharmaceuticals Inc")
             (asset "CNTA" "Centessa Pharmaceuticals plc - ADR")
             (asset "XERS" "Xeris Biopharma Holdings Inc")
             (asset "ZYME" "Zymeworks BC Inc")
             (asset "RAPT" "RAPT Therapeutics Inc")
             (asset "CELC" "Celcuity Inc")
             (asset "ABVX" "Abivax - ADR")
             (asset "MNMD" "Mind Medicine Inc")
             (asset "XFOR" "X4 Pharmaceuticals Inc")
             (asset "PLSE" "Pulse Biosciences Inc")
             (asset "CGEM" "Cullinan Therapeutics Inc")
             (asset
              "QNTM"
              "Quantum BioPharma Ltd. - Ordinary Shares - Class B (Sub Voting)")
             (asset "ALT" "Altimmune Inc")
             (asset "TERN" "Terns Pharmaceuticals Inc")
             (asset "ARQT" "Arcutis Biotherapeutics Inc")
             (asset "ACLX" "Arcellx Inc")
             (asset "OLMA" "Olema Pharmaceuticals Inc")
             (asset "VTYX" "Ventyx Biosciences Inc")
             (asset "ABSI" "Absci Corp")
             (asset "AVXL" "Anavex Life Sciences Corp")
             (asset "RZLT" "Rezolute Inc")
             (asset "TIL" "Instil Bio Inc")
             (asset "NRSN" "NeuroSense Therapeutics Ltd")
             (asset "SAVA" "Cassava Sciences Inc")
             (asset "ABCL" "AbCellera Biologics Inc")
             (asset "EVO" "Evotec SE - ADR")
             (asset "SLP" "Simulations Plus Inc.")
             (asset "GHRS" "GH Research PLC")
             (asset "DXCM" "Dexcom Inc")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset
              "BFLY"
              "Butterfly Network Inc - Ordinary Shares - Class A")
             (asset "ALIT" "Alight Inc. - Ordinary Shares - Class A")
             (asset "WELL" "Welltower Inc.")
             (asset "LLY" "Lilly(Eli) & Co")
             (asset "UNH" "Unitedhealth Group Inc")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "B" "Barrick Mining Corp.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDX" "VanEck Gold Miners ETF")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SLV" "iShares Silver Trust")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "MP" "MP Materials Corporation")
             (asset "LAC" "Lithium Americas Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset
              "TECK"
              "Teck Resources Ltd - Ordinary Shares - Class B (Sub Voting)")
             (asset "UAMY" "United States Antimony Corp")
             (asset "CPER" "United States Copper Index")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "VMC" "Vulcan Materials Co")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "SOFI" "SoFi Technologies Inc")
             (asset "AFRM" "Affirm Holdings Inc")
             (asset "UPST" "Upstart Holdings Inc")
             (asset "NU" "Nu Holdings Ltd")
             (asset "OPEN" "Opendoor Technologies Inc")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset
              "GRAB"
              "Grab Holdings Limited - Ordinary Shares - Class A")
             (asset
              "DKNG"
              "DraftKings Inc. - Ordinary Shares - Class A")
             (asset "BABA" "Alibaba Group Holding Ltd")
             (asset "PDD" "PDD Holdings Inc - ADR")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset
              "JCI"
              "Johnson Controls International plc - Registered Shares")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset
              "LPTH"
              "Lightpath Technologies, Inc. - Ordinary Shares - Class A")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset
              "PSTL"
              "Postal Realty Trust Inc - Ordinary Shares - Class A")
             (asset "CAVA" "Cava Group Inc")
             (asset
              "SMH"
              "VanEck ETF Trust - VanEck Semiconductor ETF")
             (asset
              "XLK"
              "SSgA Active Trust - State Street Technology Select Sector SPDR ETF")
             (asset
              "XLI"
              "SSgA Active Trust - State Street Industrial Select Sector SPDR ETF")
             (asset
              "XME"
              "SPDR Series Trust - State Street SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BKKT"
              "Bakkt Holdings Inc. - Ordinary Shares - Class A")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "EVTL" "Vertical Aerospace Ltd")
             (asset "QUBT" "Quantum Computing Inc")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset "BMNR" "BitMine Immersion Technologies Inc")
             (asset
              "KWEB"
              "KraneShares Trust - KraneShares CSI China Internet ETF")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "REKT"
              "Direxion Shares ETF Trust - Direxion Daily Crypto Industry Bear 1X Shares")
             (asset
              "ETH"
              "Grayscale Ethereum Staking Mini ETF - Common units of fractional undivided beneficial interest")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "SRE" "Sempra")
             (asset
              "TSLS"
              "Direxion Shares ETF Trust - Direxion Daily TSLA Bear 1X Shares")
             (asset "TSLA" "Tesla Inc")
             (asset "AAON" "AAON Inc.")
             (asset "APD" "Air Products & Chemicals Inc.")
             (asset "EQT" "EQT Corp")
             (asset "TMC" "TMC the metals company Inc")
             (asset "CSCO" "Cisco Systems, Inc.")
             (asset
              "SLVP"
              "BlackRock Institutional Trust Company N.A. - iShares MSCI Global Silver and Metals Miners ETF")])])])])]
    [(weight-equal
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
                               (cumulative-return "CORP" {:window 65}))
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
                               (cumulative-return "DIA" {:window 65}))
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
                               (cumulative-return "QQQ" {:window 15}))
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
                               (cumulative-return "HYG" {:window 10}))
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
                               (cumulative-return "HYG" {:window 10}))
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
                               (cumulative-return "XLE" {:window 30}))
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
                               (cumulative-return "XLE" {:window 30}))
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
                               (cumulative-return "USO" {:window 60}))
                              [(asset
                                "XLK"
                                "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                              [(asset
                                "BIL"
                                "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                          [(asset
                            "BIL"
                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])]))
