(defsymphony
 "FOMO NOMO - Leveraged"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
    (> (current-price "VTI") (moving-average-price "VTI" {:window 60}))
    [(weight-equal
      [(filter
        (stdev-return {:window 7})
        (select-bottom 2)
        [(weight-equal
          [(filter
            (cumulative-return {:window 2})
            (select-top 5)
            [(asset "AMAT" "Applied Materials Inc.")
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
             (asset "WOLF" "Wolfspeed Inc")
             (asset "GLW" "Corning, Inc.")
             (asset "SNDK" "Sandisk Corp")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "AI" "C3.ai Inc")
             (asset "INOD" "Innodata Inc")
             (asset "QSI" "Quantum-Si Incorporated")
             (asset "DVLT" "Datavault AI Inc.")
             (asset "PATH" "UiPath Inc")
             (asset "CFLT" "Confluent Inc")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "DUOL" "Duolingo Inc")
             (asset "AMPL" "Amplitude Inc")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc")
             (asset "FTNT" "Fortinet Inc")
             (asset "RBRK" "Rubrik Inc.")
             (asset "IBM" "International Business Machines Corp.")
             (asset "APH" "Amphenol Corp")
             (asset "HPE" "Hewlett Packard Enterprise Co")
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
             (asset "XYZ" "Block Inc")
             (asset "BKKT" "Bakkt Holdings Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset "SATL" "Satellogic Inc")
             (asset "SIDU" "Sidus Space Inc")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "AIRO" "AIRO Group Holdings Inc.")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LHX" "L3Harris Technologies Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset "CACI" "Caci International Inc.")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "CCJ" "Cameco Corp")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Uranium ETF")
             (asset "URNJ" "Sprott Junior Uranium Miners ETF")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset "CWEN" "Clearway Energy Inc")
             (asset "AMRC" "Ameresco Inc.")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset "TAN" "Invesco Solar ETF")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "FCEL" "Fuelcell Energy Inc")
             (asset "BLDP" "Ballard Power Systems Inc.")
             (asset "GEVO" "Gevo Inc")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset "HYLN" "Hyliion Holdings Corporation")
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
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset "DNA" "Ginkgo Bioworks Holdings Inc")
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
             (asset "QNTM" "Quantum BioPharma Ltd.")
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
             (asset "OMDA" "Omada Health Inc.")
             (asset "DXCM" "Dexcom Inc")
             (asset "GHRS" "GH Research PLC")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset "BFLY" "Butterfly Network Inc")
             (asset "ALIT" "Alight Inc.")
             (asset "WELL" "Welltower Inc.")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset "TECK" "Teck Resources Ltd")
             (asset "USAR" "USA Rare Earth Inc.")
             (asset "UAMY" "United States Antimony Corp")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "LIT" "Global X Lithium & Battery Tech ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "NU" "Nu Holdings Ltd")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset "GRAB" "Grab Holdings Limited")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset "JCI" "Johnson Controls International plc")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "PRLB" "Proto Labs Inc")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "VMC" "Vulcan Materials Co")
             (asset "ASPN" "Aspen Aerogels Inc.")
             (asset "NNDM" "Nano Dimension Ltd - ADR")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "LPTH" "Lightpath Technologies, Inc.")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "KOPN" "Kopin Corp.")
             (asset "WYFI" "Whitefiber Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset "PSTL" "Postal Realty Trust Inc")
             (asset "CAVA" "Cava Group Inc")
             (asset "SMH" "VanEck Semiconductor ETF")
             (asset "SMHX" "VanEck Fabless Semiconductor ETF")
             (asset "XLK" "Technology Select Sector SPDR ETF")
             (asset "XLI" "Industrial Select Sector SPDR ETF")
             (asset "XME" "SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "ETH" "Grayscale Ethereum Mini Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset "NVDL" "GraniteShares 2x Long NVDA Daily ETF")
             (asset "MULL" "GraniteShares 2x Long MU Daily ETF")
             (asset "MVLL" "GraniteShares 2x Long MRVL Daily ETF")
             (asset "AMDU" "Defiance Leveraged Long + Income AMD ETF")
             (asset "TSLL" "Direxion Daily TSLA Bull 2X Shares")
             (asset "TSMU" "GraniteShares 2x Long TSM Daily ETF")
             (asset "SMCX" "Defiance 2x Long SMCI ETF")
             (asset
              "ARMG"
              "Themes ETF Trust - Leverage Shares 2X Long ARM Daily ETF")
             (asset
              "AVGU"
              "GraniteShares ETF Trust - GraniteShares 2x Long AVGO Daily ETF")
             (asset
              "INTW"
              "GraniteShares ETF Trust - GraniteShares 2x Long INTC Daily ETF")
             (asset
              "QCML"
              "GraniteShares ETF Trust - GraniteShares 2x Long QCOM Daily ETF")
             (asset "PTIR" "GraniteShares 2x Long PLTR Daily ETF")
             (asset "NEBX" "Tradr 2X Long NBIS Daily ETF")
             (asset "NETX" "Tradr 2X Long NET Daily ETF")
             (asset "CRWU" "T-REX 2X Long CRWV Daily Target ETF")
             (asset
              "SKYU"
              "ProShares Ultra Nasdaq Cloud Computing ETF")
             (asset "PALU" "Direxion Daily PANW Bull 2X Shares")
             (asset "UCYB" "ProShares Ultra Nasdaq Cybersecurity ETF")
             (asset "TEMT" "Tradr 2X Long TEM Daily ETF")
             (asset
              "APPX"
              "Investment Managers Series Trust II - Tradr 2X Long APP Daily ETF")
             (asset
              "CRWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long CRWD Daily ETF")
             (asset
              "UBOT"
              "Direxion Shares ETF Trust - Daily Robotics, Artificial Intelligence & Automation Index Bull 2X Shares")
             (asset
              "MSFL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MSFT Daily ETF")
             (asset
              "GOOX"
              "ETF Opportunities Trust - T-Rex 2X Long Alphabet Daily Target ETF")
             (asset
              "AMZZ"
              "GraniteShares ETF Trust - GraniteShares 2x Long AMZN Daily ETF")
             (asset
              "FBL"
              "GraniteShares ETF Trust - GraniteShares 2x Long META Daily ETF")
             (asset
              "DLLL"
              "GraniteShares ETF Trust - GraniteShares 2x Long DELL Daily ETF")
             (asset
              "RDTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RDDT Daily ETF")
             (asset
              "VRTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long VRT Daily ETF")
             (asset
              "ORCU"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bull 2X ETF")
             (asset "IONL" "GraniteShares 2x Long IONQ Daily ETF")
             (asset "RGTX" "Defiance 2X Long RGTI Daily ETF")
             (asset "QBTX" "Tradr 2X Long QBTS Daily ETF")
             (asset "QUBX" "Tradr 2X Long QUBT Daily ETF")
             (asset "QPUX" "Defiance 2X Long Pure Quantum ETF")
             (asset "MSTU" "T-Rex 2X Long MSTR Daily Target ETF")
             (asset "CONL" "GraniteShares 2x Long COIN Daily ETF")
             (asset "CIFU" "T-REX 2X Long CIFR Daily Target ETF")
             (asset "BTCL" "T-Rex 2X Long Bitcoin Daily Target ETF")
             (asset "ETHU" "2x Ether ETF")
             (asset "SOLT" "2x Solana ETF")
             (asset "XRPT" "XRP 2X ETF")
             (asset
              "XXRP"
              "Listed Funds Trust - Teucrium 2x Long Daily XRP ETF")
             (asset "HOOG" "Leverage Shares 2X Long HOOD Daily ETF")
             (asset
              "MRAL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MARA Daily ETF")
             (asset
              "BEGS"
              "Collaborative Investment Series Trust - Rareview 2x Bull Cryptocurrency & Precious Metals ETF")
             (asset "RKLX" "Defiance 2X Long RKLB ETF")
             (asset
              "ASTX"
              "Investment Managers Series Trust II - Tradr 2X Long ASTS Daily ETF")
             (asset "AVXX" "Defiance 2x Long AVAV ETF")
             (asset
              "BOEU"
              "Direxion Shares ETF Trust - Direxion Daily BA Bull 2X Shares")
             (asset
              "ARCX"
              "Investment Managers Series Trust II - Tradr 2X Long ACHR Daily ETF")
             (asset
              "PONX"
              "Investment Managers Series Trust II - Tradr 2X Long PONY Daily ETF")
             (asset "ENPX" "Tradr 2X Long ENPH Daily ETF")
             (asset "IREX" "Tradr 2X Long IREN Daily ETF")
             (asset "OKLL" "Defiance 2x Long OKLO ETF")
             (asset "NNEX" "Tradr 2X Long NNE Daily ETF")
             (asset
              "SMU"
              "Investment Managers Series Trust II - Tradr 2X Long SMR Daily ETF")
             (asset "BEX" "Tradr 2X Long BE Daily ETF")
             (asset "GEVX" "Tradr 2X Long GEV Daily ETF")
             (asset "QSX" "Tradr 2X Long QS Daily ETF")
             (asset
              "CEGX"
              "Investment Managers Series Trust II - Tradr 2X Long CEG Daily ETF")
             (asset "ERX" "Direxion Daily Energy Bull 2X Shares")
             (asset "GUSH" "Direxion Daily S&P Oil & Gas Bull 2X")
             (asset "UCO" "ProShares Ultra Bloomberg Crude Oil")
             (asset "BOIL" "ProShares Ultra Bloomberg Natural Gas")
             (asset "UGL" "ProShares Ultra Gold")
             (asset "NUGT" "Direxion Daily Gold Miners Bull 2X")
             (asset "JNUG" "Direxion Daily Junior Gold Miners Bull 2X")
             (asset "AGQ" "ProShares Ultra Silver")
             (asset "CPXR" "USCF Daily Target 2X Copper Index ETF")
             (asset "LLYX" "Defiance 2X Long LLY ETF")
             (asset
              "UNHG"
              "Themes ETF Trust - Leverage Shares 2X Long UNH Daily ETF")
             (asset
              "UPSX"
              "Investment Managers Series Trust II - Tradr 2X Long UPST Daily ETF")
             (asset
              "BABX"
              "GraniteShares ETF Trust - GraniteShares 2x Long BABA Daily ETF")
             (asset
              "PDDL"
              "GraniteShares ETF Trust - GraniteShares 2x Long PDD Daily ETF")
             (asset
              "RVNL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RIVN Daily ETF")
             (asset "NVDQ" "T-Rex 2X Inverse NVIDIA Daily Target ETF")
             (asset "DAMD" "Defiance 2X Short AMD ETF")
             (asset "STSM" "Defiance 2X Short TSM ETF")
             (asset "SMCZ" "Defiance 2X Short SMCI ETF")
             (asset "PLTZ" "Defiance 2x Short PLTR ETF")
             (asset "CORD" "T-REX 2X Inverse CRWV Daily Target ETF")
             (asset
              "ORCS"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bear 1X ETF")
             (asset "RGTZ" "Defiance 2x Short RGTI ETF")
             (asset "IONZ" "Defiance 2x Short IONQ ETF")
             (asset "QBTZ" "Defiance 2x Short QBTS ETF")
             (asset "MSTZ" "T-Rex 2X Inverse MSTR Daily Target ETF")
             (asset "CONI" "GraniteShares 2x Short COIN Daily ETF")
             (asset "BITI" "ProShares Short Bitcoin ETF")
             (asset
              "SBIT"
              "ProShares Trust - ProShares UltraShort Bitcoin ETF")
             (asset "BTCZ" "T-Rex 2X Inverse Bitcoin Daily Target ETF")
             (asset "ETHD" "ProShares UltraShort Ether ETF")
             (asset "SOLZ" "Solana ETF")
             (asset "XRPZ" "Franklin XRP Trust")
             (asset "HOOZ" "Defiance 2X Short HOOD ETF")
             (asset "REKT" "Direxion Daily Crypto Industry Bear 1X")
             (asset "RKLZ" "Defiance 2x Short RKLB ETF")
             (asset "OKLS" "Defiance 2X Short OKLO ETF")
             (asset "ERY" "Direxion Daily Energy Bear -2X Shares")
             (asset "DRIP" "Direxion Daily S&P Oil & Gas Bear 2X")
             (asset "SCO" "ProShares UltraShort Bloomberg Crude Oil")
             (asset
              "KOLD"
              "ProShares UltraShort Bloomberg Natural Gas")
             (asset
              "GLL"
              "ProShares Trust - ProShares UltraShort Gold -2x Shares")
             (asset "DUST" "Direxion Daily Gold Miners Bear -2X")
             (asset "ZSL" "ProShares UltraShort Silver")
             (asset "LLYZ" "Defiance 2X Short LLY ETF")
             (asset
              "BITX"
              "Volatility Shares Trust - 2x Bitcoin Strategy ETF")
             (asset
              "AAPU"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bull 2X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "UTSL"
              "Direxion Shares ETF Trust - Direxion Daily Utilities Bull 3X Shares")
             (asset
              "DFEN"
              "Direxion Shares ETF Trust - Direxion Daily Aerospace & Defense Bull 3X Shares")
             (asset
              "LRCU"
              "Investment Managers Series Trust II - Tradr 2X Long LRCX Daily ETF")
             (asset
              "LABX"
              "Investment Managers Series Trust II - Tradr 2X Long ALAB Daily ETF")
             (asset
              "CRDU"
              "Investment Managers Series Trust II - Tradr 2X Long CRDO Daily ETF")
             (asset
              "CRCD"
              "ETF Opportunities Trust - T-REX 2X Inverse CRCL Daily Target ETF")
             (asset
              "DOGD"
              "Investment Managers Series Trust II - Tradr 2X Long DDOG Daily ETF")
             (asset
              "MDBX"
              "Investment Managers Series Trust II - Tradr 2X Long MDB Daily ETF")
             (asset
              "CLSX"
              "Investment Managers Series Trust II - Tradr 2X Long CLSK Daily ETF")
             (asset
              "COZX"
              "Investment Managers Series Trust II - Tradr 2X Long CORZ Daily ETF")
             (asset
              "CSEX"
              "Investment Managers Series Trust II - Tradr 2X Long CLS Daily ETF")
             (asset
              "JOBX"
              "Investment Managers Series Trust II - Tradr 2X Long JOBY Daily ETF")
             (asset
              "OPEX"
              "Investment Managers Series Trust II - Tradr 2X Long OPEN Daily ETF")
             (asset
              "WULX"
              "Investment Managers Series Trust II - Tradr 2X Long WULF Daily ETF")
             (asset
              "ANEL"
              "Tidal Trust II - Defiance Daily Target 2x Long ANET ETF")
             (asset
              "VSTL"
              "Tidal Trust II - Defiance Daily Target 2X Long VST ETF")
             (asset
              "SOUX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOUN ETF")
             (asset
              "RIOX"
              "Tidal Trust II - Defiance Daily Target 2X Long RIOT ETF")
             (asset
              "BU"
              "Tidal Trust II - Defiance Daily Target 2X Long BU ETF")
             (asset
              "SNOU"
              "ETF Opportunities Trust - T-REX 2X Long SNOW Daily Target ETF")
             (asset
              "DKUP"
              "ETF Opportunities Trust - T-REX 2X Long DKNG Daily Target ETF")
             (asset
              "AFRU"
              "ETF Opportunities Trust - T-REX 2X Long AFRM Daily Target ETF")
             (asset
              "KTUP"
              "Investment Managers Series Trust II - T-REX 2X Long KTOS Daily Target ETF")
             (asset
              "GLXU"
              "ETF Opportunities Trust - T-REX 2X Long GLXY Daily Target ETF")
             (asset
              "CCUP"
              "ETF Opportunities Trust - T-REX 2X Long CRCL Daily Target ETF")
             (asset
              "TSLQ"
              "Investment Managers Series Trust II - Tradr 2X Short TSLA Daily ETF")
             (asset
              "NVDS"
              "Investment Managers Series Trust II - Tradr 1.5X Short NVDA Daily ETF")
             (asset
              "SOFX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOFI ETF")
             (asset
              "MPL"
              "Tidal Trust II - Defiance Daily Target 2X Long MP ETF")
             (asset
              "CRMG"
              "Themes ETF Trust - Leverage Shares 2X Long CRM Daily ETF")
             (asset
              "ISUL"
              "GraniteShares ETF Trust - GraniteShares 2x Long ISRG Daily ETF")
             (asset
              "NOWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long NOW Daily ETF")
             (asset
              "PYPG"
              "Themes ETF Trust - Leverage Shares 2X Long PYPL Daily ETF")
             (asset
              "NFXS"
              "Direxion Shares ETF Trust - Direxion Daily NFLX Bear 1X Shares")
             (asset
              "BOED"
              "Direxion Shares ETF Trust - Direxion Daily BA Bear 1X Shares")
             (asset
              "LMTS"
              "Direxion Shares ETF Trust - Direxion Daily LMT Bear 1X ETF")
             (asset
              "XOMZ"
              "Direxion Shares ETF Trust - Direxion Daily XOM Bear 1X Shares")
             (asset
              "PALD"
              "Direxion Shares ETF Trust - Direxion Daily PANW Bear 1X Shares")
             (asset
              "AVS"
              "Direxion Shares ETF Trust - Direxion Daily AVGO Bear 1X Shares")
             (asset
              "QCMD"
              "Direxion Shares ETF Trust - Direxion Daily QCOM Bear 1X ETF")
             (asset
              "MUD"
              "Direxion Shares ETF Trust - Direxion Daily MU Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "CSCS"
              "Direxion Shares ETF Trust - Direxion Daily CSCO Bear 1X ETF")
             (asset
              "QQQD"
              "Direxion Shares ETF Trust - Direxion Daily Magnificent 7 Bear 1X Shares")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "BIL" "SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "LACG"
              "Themes ETF Trust - Leverage Shares 2X Long LAC Daily ETF")
             (asset
              "BEG"
              "Themes ETF Trust - Leverage Shares 2x Long BE Daily ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset
              "INDI"
              "Indie Semiconductor Inc - Ordinary Shares - Class A")
             (asset "GSIT" "GSI Technology Inc")
             (asset "SLS" "SELLAS Life Sciences Group Inc")
             (asset "SRFM" "Surf Air Mobility Inc")
             (asset
              "PXIU"
              "ETF Opportunities Trust - T-REX 2X Long UPXI Daily Target ETF")
             (asset "DRUG" "Bright Minds Biosciences Inc")
             (asset
              "CWEB"
              "Direxion Shares ETF Trust - Direxion Daily CSI China Internet Index Bull 2X Shares")
             (asset
              "XPP"
              "ProShares Trust - ProShares Ultra FTSE China 50 2x Shares")
             (asset
              "CHAU"
              "Direxion Shares ETF Trust - Direxion Daily CSI 300 China A Share Bull 2X Shares")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")])])
         (weight-equal
          [(filter
            (stdev-return {:window 2})
            (select-top 5)
            [(asset "AMAT" "Applied Materials Inc.")
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
             (asset "WOLF" "Wolfspeed Inc")
             (asset "GLW" "Corning, Inc.")
             (asset "SNDK" "Sandisk Corp")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "AI" "C3.ai Inc")
             (asset "INOD" "Innodata Inc")
             (asset "QSI" "Quantum-Si Incorporated")
             (asset "DVLT" "Datavault AI Inc.")
             (asset "PATH" "UiPath Inc")
             (asset "CFLT" "Confluent Inc")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "DUOL" "Duolingo Inc")
             (asset "AMPL" "Amplitude Inc")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc")
             (asset "FTNT" "Fortinet Inc")
             (asset "RBRK" "Rubrik Inc.")
             (asset "IBM" "International Business Machines Corp.")
             (asset "APH" "Amphenol Corp")
             (asset "HPE" "Hewlett Packard Enterprise Co")
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
             (asset "XYZ" "Block Inc")
             (asset "BKKT" "Bakkt Holdings Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset "SATL" "Satellogic Inc")
             (asset "SIDU" "Sidus Space Inc")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "AIRO" "AIRO Group Holdings Inc.")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LHX" "L3Harris Technologies Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset "CACI" "Caci International Inc.")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "CCJ" "Cameco Corp")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Uranium ETF")
             (asset "URNJ" "Sprott Junior Uranium Miners ETF")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset "CWEN" "Clearway Energy Inc")
             (asset "AMRC" "Ameresco Inc.")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset "TAN" "Invesco Solar ETF")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "FCEL" "Fuelcell Energy Inc")
             (asset "BLDP" "Ballard Power Systems Inc.")
             (asset "GEVO" "Gevo Inc")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset "HYLN" "Hyliion Holdings Corporation")
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
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset "DNA" "Ginkgo Bioworks Holdings Inc")
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
             (asset "QNTM" "Quantum BioPharma Ltd.")
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
             (asset "OMDA" "Omada Health Inc.")
             (asset "DXCM" "Dexcom Inc")
             (asset "GHRS" "GH Research PLC")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset "BFLY" "Butterfly Network Inc")
             (asset "ALIT" "Alight Inc.")
             (asset "WELL" "Welltower Inc.")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset "TECK" "Teck Resources Ltd")
             (asset "USAR" "USA Rare Earth Inc.")
             (asset "UAMY" "United States Antimony Corp")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "LIT" "Global X Lithium & Battery Tech ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "NU" "Nu Holdings Ltd")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset "GRAB" "Grab Holdings Limited")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset "JCI" "Johnson Controls International plc")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "PRLB" "Proto Labs Inc")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "VMC" "Vulcan Materials Co")
             (asset "ASPN" "Aspen Aerogels Inc.")
             (asset "NNDM" "Nano Dimension Ltd - ADR")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "LPTH" "Lightpath Technologies, Inc.")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "KOPN" "Kopin Corp.")
             (asset "WYFI" "Whitefiber Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset "PSTL" "Postal Realty Trust Inc")
             (asset "CAVA" "Cava Group Inc")
             (asset "SMH" "VanEck Semiconductor ETF")
             (asset "SMHX" "VanEck Fabless Semiconductor ETF")
             (asset "XLK" "Technology Select Sector SPDR ETF")
             (asset "XLI" "Industrial Select Sector SPDR ETF")
             (asset "XME" "SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "ETH" "Grayscale Ethereum Mini Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset "NVDL" "GraniteShares 2x Long NVDA Daily ETF")
             (asset "MULL" "GraniteShares 2x Long MU Daily ETF")
             (asset "MVLL" "GraniteShares 2x Long MRVL Daily ETF")
             (asset "AMDU" "Defiance Leveraged Long + Income AMD ETF")
             (asset "TSLL" "Direxion Daily TSLA Bull 2X Shares")
             (asset "TSMU" "GraniteShares 2x Long TSM Daily ETF")
             (asset "SMCX" "Defiance 2x Long SMCI ETF")
             (asset
              "ARMG"
              "Themes ETF Trust - Leverage Shares 2X Long ARM Daily ETF")
             (asset
              "AVGU"
              "GraniteShares ETF Trust - GraniteShares 2x Long AVGO Daily ETF")
             (asset
              "INTW"
              "GraniteShares ETF Trust - GraniteShares 2x Long INTC Daily ETF")
             (asset
              "QCML"
              "GraniteShares ETF Trust - GraniteShares 2x Long QCOM Daily ETF")
             (asset "PTIR" "GraniteShares 2x Long PLTR Daily ETF")
             (asset "NEBX" "Tradr 2X Long NBIS Daily ETF")
             (asset "NETX" "Tradr 2X Long NET Daily ETF")
             (asset "CRWU" "T-REX 2X Long CRWV Daily Target ETF")
             (asset
              "SKYU"
              "ProShares Ultra Nasdaq Cloud Computing ETF")
             (asset "PALU" "Direxion Daily PANW Bull 2X Shares")
             (asset "UCYB" "ProShares Ultra Nasdaq Cybersecurity ETF")
             (asset "TEMT" "Tradr 2X Long TEM Daily ETF")
             (asset
              "APPX"
              "Investment Managers Series Trust II - Tradr 2X Long APP Daily ETF")
             (asset
              "CRWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long CRWD Daily ETF")
             (asset
              "UBOT"
              "Direxion Shares ETF Trust - Daily Robotics, Artificial Intelligence & Automation Index Bull 2X Shares")
             (asset
              "MSFL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MSFT Daily ETF")
             (asset
              "GOOX"
              "ETF Opportunities Trust - T-Rex 2X Long Alphabet Daily Target ETF")
             (asset
              "AMZZ"
              "GraniteShares ETF Trust - GraniteShares 2x Long AMZN Daily ETF")
             (asset
              "FBL"
              "GraniteShares ETF Trust - GraniteShares 2x Long META Daily ETF")
             (asset
              "DLLL"
              "GraniteShares ETF Trust - GraniteShares 2x Long DELL Daily ETF")
             (asset
              "RDTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RDDT Daily ETF")
             (asset
              "VRTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long VRT Daily ETF")
             (asset
              "ORCU"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bull 2X ETF")
             (asset "IONL" "GraniteShares 2x Long IONQ Daily ETF")
             (asset "RGTX" "Defiance 2X Long RGTI Daily ETF")
             (asset "QBTX" "Tradr 2X Long QBTS Daily ETF")
             (asset "QUBX" "Tradr 2X Long QUBT Daily ETF")
             (asset "QPUX" "Defiance 2X Long Pure Quantum ETF")
             (asset "MSTU" "T-Rex 2X Long MSTR Daily Target ETF")
             (asset "CONL" "GraniteShares 2x Long COIN Daily ETF")
             (asset "CIFU" "T-REX 2X Long CIFR Daily Target ETF")
             (asset "BTCL" "T-Rex 2X Long Bitcoin Daily Target ETF")
             (asset "ETHU" "2x Ether ETF")
             (asset "SOLT" "2x Solana ETF")
             (asset "XRPT" "XRP 2X ETF")
             (asset
              "XXRP"
              "Listed Funds Trust - Teucrium 2x Long Daily XRP ETF")
             (asset "HOOG" "Leverage Shares 2X Long HOOD Daily ETF")
             (asset
              "MRAL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MARA Daily ETF")
             (asset
              "BEGS"
              "Collaborative Investment Series Trust - Rareview 2x Bull Cryptocurrency & Precious Metals ETF")
             (asset "RKLX" "Defiance 2X Long RKLB ETF")
             (asset
              "ASTX"
              "Investment Managers Series Trust II - Tradr 2X Long ASTS Daily ETF")
             (asset "AVXX" "Defiance 2x Long AVAV ETF")
             (asset
              "BOEU"
              "Direxion Shares ETF Trust - Direxion Daily BA Bull 2X Shares")
             (asset
              "ARCX"
              "Investment Managers Series Trust II - Tradr 2X Long ACHR Daily ETF")
             (asset
              "PONX"
              "Investment Managers Series Trust II - Tradr 2X Long PONY Daily ETF")
             (asset "ENPX" "Tradr 2X Long ENPH Daily ETF")
             (asset "IREX" "Tradr 2X Long IREN Daily ETF")
             (asset "OKLL" "Defiance 2x Long OKLO ETF")
             (asset "NNEX" "Tradr 2X Long NNE Daily ETF")
             (asset
              "SMU"
              "Investment Managers Series Trust II - Tradr 2X Long SMR Daily ETF")
             (asset "BEX" "Tradr 2X Long BE Daily ETF")
             (asset "GEVX" "Tradr 2X Long GEV Daily ETF")
             (asset "QSX" "Tradr 2X Long QS Daily ETF")
             (asset
              "CEGX"
              "Investment Managers Series Trust II - Tradr 2X Long CEG Daily ETF")
             (asset "ERX" "Direxion Daily Energy Bull 2X Shares")
             (asset "GUSH" "Direxion Daily S&P Oil & Gas Bull 2X")
             (asset "UCO" "ProShares Ultra Bloomberg Crude Oil")
             (asset "BOIL" "ProShares Ultra Bloomberg Natural Gas")
             (asset "UGL" "ProShares Ultra Gold")
             (asset "NUGT" "Direxion Daily Gold Miners Bull 2X")
             (asset "JNUG" "Direxion Daily Junior Gold Miners Bull 2X")
             (asset "AGQ" "ProShares Ultra Silver")
             (asset "CPXR" "USCF Daily Target 2X Copper Index ETF")
             (asset "LLYX" "Defiance 2X Long LLY ETF")
             (asset
              "UNHG"
              "Themes ETF Trust - Leverage Shares 2X Long UNH Daily ETF")
             (asset
              "UPSX"
              "Investment Managers Series Trust II - Tradr 2X Long UPST Daily ETF")
             (asset
              "BABX"
              "GraniteShares ETF Trust - GraniteShares 2x Long BABA Daily ETF")
             (asset
              "PDDL"
              "GraniteShares ETF Trust - GraniteShares 2x Long PDD Daily ETF")
             (asset
              "RVNL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RIVN Daily ETF")
             (asset "NVDQ" "T-Rex 2X Inverse NVIDIA Daily Target ETF")
             (asset "DAMD" "Defiance 2X Short AMD ETF")
             (asset "STSM" "Defiance 2X Short TSM ETF")
             (asset "SMCZ" "Defiance 2X Short SMCI ETF")
             (asset "PLTZ" "Defiance 2x Short PLTR ETF")
             (asset "CORD" "T-REX 2X Inverse CRWV Daily Target ETF")
             (asset
              "ORCS"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bear 1X ETF")
             (asset "RGTZ" "Defiance 2x Short RGTI ETF")
             (asset "IONZ" "Defiance 2x Short IONQ ETF")
             (asset "QBTZ" "Defiance 2x Short QBTS ETF")
             (asset "MSTZ" "T-Rex 2X Inverse MSTR Daily Target ETF")
             (asset "CONI" "GraniteShares 2x Short COIN Daily ETF")
             (asset "BITI" "ProShares Short Bitcoin ETF")
             (asset
              "SBIT"
              "ProShares Trust - ProShares UltraShort Bitcoin ETF")
             (asset "BTCZ" "T-Rex 2X Inverse Bitcoin Daily Target ETF")
             (asset "ETHD" "ProShares UltraShort Ether ETF")
             (asset "SOLZ" "Solana ETF")
             (asset "XRPZ" "Franklin XRP Trust")
             (asset "HOOZ" "Defiance 2X Short HOOD ETF")
             (asset "REKT" "Direxion Daily Crypto Industry Bear 1X")
             (asset "RKLZ" "Defiance 2x Short RKLB ETF")
             (asset "OKLS" "Defiance 2X Short OKLO ETF")
             (asset "ERY" "Direxion Daily Energy Bear -2X Shares")
             (asset "DRIP" "Direxion Daily S&P Oil & Gas Bear 2X")
             (asset "SCO" "ProShares UltraShort Bloomberg Crude Oil")
             (asset
              "KOLD"
              "ProShares UltraShort Bloomberg Natural Gas")
             (asset
              "GLL"
              "ProShares Trust - ProShares UltraShort Gold -2x Shares")
             (asset "DUST" "Direxion Daily Gold Miners Bear -2X")
             (asset "ZSL" "ProShares UltraShort Silver")
             (asset "LLYZ" "Defiance 2X Short LLY ETF")
             (asset
              "BITX"
              "Volatility Shares Trust - 2x Bitcoin Strategy ETF")
             (asset
              "AAPU"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bull 2X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "UTSL"
              "Direxion Shares ETF Trust - Direxion Daily Utilities Bull 3X Shares")
             (asset
              "DFEN"
              "Direxion Shares ETF Trust - Direxion Daily Aerospace & Defense Bull 3X Shares")
             (asset
              "LRCU"
              "Investment Managers Series Trust II - Tradr 2X Long LRCX Daily ETF")
             (asset
              "LABX"
              "Investment Managers Series Trust II - Tradr 2X Long ALAB Daily ETF")
             (asset
              "CRDU"
              "Investment Managers Series Trust II - Tradr 2X Long CRDO Daily ETF")
             (asset
              "CRCD"
              "ETF Opportunities Trust - T-REX 2X Inverse CRCL Daily Target ETF")
             (asset
              "DOGD"
              "Investment Managers Series Trust II - Tradr 2X Long DDOG Daily ETF")
             (asset
              "MDBX"
              "Investment Managers Series Trust II - Tradr 2X Long MDB Daily ETF")
             (asset
              "CLSX"
              "Investment Managers Series Trust II - Tradr 2X Long CLSK Daily ETF")
             (asset
              "COZX"
              "Investment Managers Series Trust II - Tradr 2X Long CORZ Daily ETF")
             (asset
              "CSEX"
              "Investment Managers Series Trust II - Tradr 2X Long CLS Daily ETF")
             (asset
              "JOBX"
              "Investment Managers Series Trust II - Tradr 2X Long JOBY Daily ETF")
             (asset
              "OPEX"
              "Investment Managers Series Trust II - Tradr 2X Long OPEN Daily ETF")
             (asset
              "WULX"
              "Investment Managers Series Trust II - Tradr 2X Long WULF Daily ETF")
             (asset
              "ANEL"
              "Tidal Trust II - Defiance Daily Target 2x Long ANET ETF")
             (asset
              "VSTL"
              "Tidal Trust II - Defiance Daily Target 2X Long VST ETF")
             (asset
              "SOUX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOUN ETF")
             (asset
              "RIOX"
              "Tidal Trust II - Defiance Daily Target 2X Long RIOT ETF")
             (asset
              "BU"
              "Tidal Trust II - Defiance Daily Target 2X Long BU ETF")
             (asset
              "SNOU"
              "ETF Opportunities Trust - T-REX 2X Long SNOW Daily Target ETF")
             (asset
              "DKUP"
              "ETF Opportunities Trust - T-REX 2X Long DKNG Daily Target ETF")
             (asset
              "AFRU"
              "ETF Opportunities Trust - T-REX 2X Long AFRM Daily Target ETF")
             (asset
              "KTUP"
              "Investment Managers Series Trust II - T-REX 2X Long KTOS Daily Target ETF")
             (asset
              "GLXU"
              "ETF Opportunities Trust - T-REX 2X Long GLXY Daily Target ETF")
             (asset
              "CCUP"
              "ETF Opportunities Trust - T-REX 2X Long CRCL Daily Target ETF")
             (asset
              "TSLQ"
              "Investment Managers Series Trust II - Tradr 2X Short TSLA Daily ETF")
             (asset
              "NVDS"
              "Investment Managers Series Trust II - Tradr 1.5X Short NVDA Daily ETF")
             (asset
              "SOFX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOFI ETF")
             (asset
              "MPL"
              "Tidal Trust II - Defiance Daily Target 2X Long MP ETF")
             (asset
              "CRMG"
              "Themes ETF Trust - Leverage Shares 2X Long CRM Daily ETF")
             (asset
              "ISUL"
              "GraniteShares ETF Trust - GraniteShares 2x Long ISRG Daily ETF")
             (asset
              "NOWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long NOW Daily ETF")
             (asset
              "PYPG"
              "Themes ETF Trust - Leverage Shares 2X Long PYPL Daily ETF")
             (asset
              "NFXS"
              "Direxion Shares ETF Trust - Direxion Daily NFLX Bear 1X Shares")
             (asset
              "BOED"
              "Direxion Shares ETF Trust - Direxion Daily BA Bear 1X Shares")
             (asset
              "LMTS"
              "Direxion Shares ETF Trust - Direxion Daily LMT Bear 1X ETF")
             (asset
              "XOMZ"
              "Direxion Shares ETF Trust - Direxion Daily XOM Bear 1X Shares")
             (asset
              "PALD"
              "Direxion Shares ETF Trust - Direxion Daily PANW Bear 1X Shares")
             (asset
              "AVS"
              "Direxion Shares ETF Trust - Direxion Daily AVGO Bear 1X Shares")
             (asset
              "QCMD"
              "Direxion Shares ETF Trust - Direxion Daily QCOM Bear 1X ETF")
             (asset
              "MUD"
              "Direxion Shares ETF Trust - Direxion Daily MU Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "CSCS"
              "Direxion Shares ETF Trust - Direxion Daily CSCO Bear 1X ETF")
             (asset
              "QQQD"
              "Direxion Shares ETF Trust - Direxion Daily Magnificent 7 Bear 1X Shares")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "BIL" "SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "LACG"
              "Themes ETF Trust - Leverage Shares 2X Long LAC Daily ETF")
             (asset
              "BEG"
              "Themes ETF Trust - Leverage Shares 2x Long BE Daily ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset
              "INDI"
              "Indie Semiconductor Inc - Ordinary Shares - Class A")
             (asset "GSIT" "GSI Technology Inc")
             (asset "SLS" "SELLAS Life Sciences Group Inc")
             (asset "SRFM" "Surf Air Mobility Inc")
             (asset
              "PXIU"
              "ETF Opportunities Trust - T-REX 2X Long UPXI Daily Target ETF")
             (asset "DRUG" "Bright Minds Biosciences Inc")
             (asset
              "CWEB"
              "Direxion Shares ETF Trust - Direxion Daily CSI China Internet Index Bull 2X Shares")
             (asset
              "XPP"
              "ProShares Trust - ProShares Ultra FTSE China 50 2x Shares")
             (asset
              "CHAU"
              "Direxion Shares ETF Trust - Direxion Daily CSI 300 China A Share Bull 2X Shares")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")])])
         (weight-equal
          [(filter
            (stdev-return {:window 2})
            (select-top 3)
            [(asset "AMAT" "Applied Materials Inc.")
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
             (asset "WOLF" "Wolfspeed Inc")
             (asset "GLW" "Corning, Inc.")
             (asset "SNDK" "Sandisk Corp")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "AI" "C3.ai Inc")
             (asset "INOD" "Innodata Inc")
             (asset "QSI" "Quantum-Si Incorporated")
             (asset "DVLT" "Datavault AI Inc.")
             (asset "PATH" "UiPath Inc")
             (asset "CFLT" "Confluent Inc")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "DUOL" "Duolingo Inc")
             (asset "AMPL" "Amplitude Inc")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc")
             (asset "FTNT" "Fortinet Inc")
             (asset "RBRK" "Rubrik Inc.")
             (asset "IBM" "International Business Machines Corp.")
             (asset "APH" "Amphenol Corp")
             (asset "HPE" "Hewlett Packard Enterprise Co")
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
             (asset "XYZ" "Block Inc")
             (asset "BKKT" "Bakkt Holdings Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset "SATL" "Satellogic Inc")
             (asset "SIDU" "Sidus Space Inc")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "AIRO" "AIRO Group Holdings Inc.")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LHX" "L3Harris Technologies Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset "CACI" "Caci International Inc.")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "CCJ" "Cameco Corp")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Uranium ETF")
             (asset "URNJ" "Sprott Junior Uranium Miners ETF")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset "CWEN" "Clearway Energy Inc")
             (asset "AMRC" "Ameresco Inc.")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset "TAN" "Invesco Solar ETF")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "FCEL" "Fuelcell Energy Inc")
             (asset "BLDP" "Ballard Power Systems Inc.")
             (asset "GEVO" "Gevo Inc")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset "HYLN" "Hyliion Holdings Corporation")
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
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset "DNA" "Ginkgo Bioworks Holdings Inc")
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
             (asset "QNTM" "Quantum BioPharma Ltd.")
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
             (asset "OMDA" "Omada Health Inc.")
             (asset "DXCM" "Dexcom Inc")
             (asset "GHRS" "GH Research PLC")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset "BFLY" "Butterfly Network Inc")
             (asset "ALIT" "Alight Inc.")
             (asset "WELL" "Welltower Inc.")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset "TECK" "Teck Resources Ltd")
             (asset "USAR" "USA Rare Earth Inc.")
             (asset "UAMY" "United States Antimony Corp")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "LIT" "Global X Lithium & Battery Tech ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "NU" "Nu Holdings Ltd")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset "GRAB" "Grab Holdings Limited")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset "JCI" "Johnson Controls International plc")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "PRLB" "Proto Labs Inc")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "VMC" "Vulcan Materials Co")
             (asset "ASPN" "Aspen Aerogels Inc.")
             (asset "NNDM" "Nano Dimension Ltd - ADR")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "LPTH" "Lightpath Technologies, Inc.")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "KOPN" "Kopin Corp.")
             (asset "WYFI" "Whitefiber Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset "PSTL" "Postal Realty Trust Inc")
             (asset "CAVA" "Cava Group Inc")
             (asset "SMH" "VanEck Semiconductor ETF")
             (asset "SMHX" "VanEck Fabless Semiconductor ETF")
             (asset "XLK" "Technology Select Sector SPDR ETF")
             (asset "XLI" "Industrial Select Sector SPDR ETF")
             (asset "XME" "SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "ETH" "Grayscale Ethereum Mini Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset "NVDL" "GraniteShares 2x Long NVDA Daily ETF")
             (asset "MULL" "GraniteShares 2x Long MU Daily ETF")
             (asset "MVLL" "GraniteShares 2x Long MRVL Daily ETF")
             (asset "AMDU" "Defiance Leveraged Long + Income AMD ETF")
             (asset "TSLL" "Direxion Daily TSLA Bull 2X Shares")
             (asset "TSMU" "GraniteShares 2x Long TSM Daily ETF")
             (asset "SMCX" "Defiance 2x Long SMCI ETF")
             (asset
              "ARMG"
              "Themes ETF Trust - Leverage Shares 2X Long ARM Daily ETF")
             (asset
              "AVGU"
              "GraniteShares ETF Trust - GraniteShares 2x Long AVGO Daily ETF")
             (asset
              "INTW"
              "GraniteShares ETF Trust - GraniteShares 2x Long INTC Daily ETF")
             (asset
              "QCML"
              "GraniteShares ETF Trust - GraniteShares 2x Long QCOM Daily ETF")
             (asset "PTIR" "GraniteShares 2x Long PLTR Daily ETF")
             (asset "NEBX" "Tradr 2X Long NBIS Daily ETF")
             (asset "NETX" "Tradr 2X Long NET Daily ETF")
             (asset "CRWU" "T-REX 2X Long CRWV Daily Target ETF")
             (asset
              "SKYU"
              "ProShares Ultra Nasdaq Cloud Computing ETF")
             (asset "PALU" "Direxion Daily PANW Bull 2X Shares")
             (asset "UCYB" "ProShares Ultra Nasdaq Cybersecurity ETF")
             (asset "TEMT" "Tradr 2X Long TEM Daily ETF")
             (asset
              "APPX"
              "Investment Managers Series Trust II - Tradr 2X Long APP Daily ETF")
             (asset
              "CRWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long CRWD Daily ETF")
             (asset
              "UBOT"
              "Direxion Shares ETF Trust - Daily Robotics, Artificial Intelligence & Automation Index Bull 2X Shares")
             (asset
              "MSFL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MSFT Daily ETF")
             (asset
              "GOOX"
              "ETF Opportunities Trust - T-Rex 2X Long Alphabet Daily Target ETF")
             (asset
              "AMZZ"
              "GraniteShares ETF Trust - GraniteShares 2x Long AMZN Daily ETF")
             (asset
              "FBL"
              "GraniteShares ETF Trust - GraniteShares 2x Long META Daily ETF")
             (asset
              "DLLL"
              "GraniteShares ETF Trust - GraniteShares 2x Long DELL Daily ETF")
             (asset
              "RDTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RDDT Daily ETF")
             (asset
              "VRTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long VRT Daily ETF")
             (asset
              "ORCU"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bull 2X ETF")
             (asset "IONL" "GraniteShares 2x Long IONQ Daily ETF")
             (asset "RGTX" "Defiance 2X Long RGTI Daily ETF")
             (asset "QBTX" "Tradr 2X Long QBTS Daily ETF")
             (asset "QUBX" "Tradr 2X Long QUBT Daily ETF")
             (asset "QPUX" "Defiance 2X Long Pure Quantum ETF")
             (asset "MSTU" "T-Rex 2X Long MSTR Daily Target ETF")
             (asset "CONL" "GraniteShares 2x Long COIN Daily ETF")
             (asset "CIFU" "T-REX 2X Long CIFR Daily Target ETF")
             (asset "BTCL" "T-Rex 2X Long Bitcoin Daily Target ETF")
             (asset "ETHU" "2x Ether ETF")
             (asset "SOLT" "2x Solana ETF")
             (asset "XRPT" "XRP 2X ETF")
             (asset
              "XXRP"
              "Listed Funds Trust - Teucrium 2x Long Daily XRP ETF")
             (asset "HOOG" "Leverage Shares 2X Long HOOD Daily ETF")
             (asset
              "MRAL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MARA Daily ETF")
             (asset
              "BEGS"
              "Collaborative Investment Series Trust - Rareview 2x Bull Cryptocurrency & Precious Metals ETF")
             (asset "RKLX" "Defiance 2X Long RKLB ETF")
             (asset
              "ASTX"
              "Investment Managers Series Trust II - Tradr 2X Long ASTS Daily ETF")
             (asset "AVXX" "Defiance 2x Long AVAV ETF")
             (asset
              "BOEU"
              "Direxion Shares ETF Trust - Direxion Daily BA Bull 2X Shares")
             (asset
              "ARCX"
              "Investment Managers Series Trust II - Tradr 2X Long ACHR Daily ETF")
             (asset
              "PONX"
              "Investment Managers Series Trust II - Tradr 2X Long PONY Daily ETF")
             (asset "ENPX" "Tradr 2X Long ENPH Daily ETF")
             (asset "IREX" "Tradr 2X Long IREN Daily ETF")
             (asset "OKLL" "Defiance 2x Long OKLO ETF")
             (asset "NNEX" "Tradr 2X Long NNE Daily ETF")
             (asset
              "SMU"
              "Investment Managers Series Trust II - Tradr 2X Long SMR Daily ETF")
             (asset "BEX" "Tradr 2X Long BE Daily ETF")
             (asset "GEVX" "Tradr 2X Long GEV Daily ETF")
             (asset "QSX" "Tradr 2X Long QS Daily ETF")
             (asset
              "CEGX"
              "Investment Managers Series Trust II - Tradr 2X Long CEG Daily ETF")
             (asset "ERX" "Direxion Daily Energy Bull 2X Shares")
             (asset "GUSH" "Direxion Daily S&P Oil & Gas Bull 2X")
             (asset "UCO" "ProShares Ultra Bloomberg Crude Oil")
             (asset "BOIL" "ProShares Ultra Bloomberg Natural Gas")
             (asset "UGL" "ProShares Ultra Gold")
             (asset "NUGT" "Direxion Daily Gold Miners Bull 2X")
             (asset "JNUG" "Direxion Daily Junior Gold Miners Bull 2X")
             (asset "AGQ" "ProShares Ultra Silver")
             (asset "CPXR" "USCF Daily Target 2X Copper Index ETF")
             (asset "LLYX" "Defiance 2X Long LLY ETF")
             (asset
              "UNHG"
              "Themes ETF Trust - Leverage Shares 2X Long UNH Daily ETF")
             (asset
              "UPSX"
              "Investment Managers Series Trust II - Tradr 2X Long UPST Daily ETF")
             (asset
              "BABX"
              "GraniteShares ETF Trust - GraniteShares 2x Long BABA Daily ETF")
             (asset
              "PDDL"
              "GraniteShares ETF Trust - GraniteShares 2x Long PDD Daily ETF")
             (asset
              "RVNL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RIVN Daily ETF")
             (asset "NVDQ" "T-Rex 2X Inverse NVIDIA Daily Target ETF")
             (asset "DAMD" "Defiance 2X Short AMD ETF")
             (asset "STSM" "Defiance 2X Short TSM ETF")
             (asset "SMCZ" "Defiance 2X Short SMCI ETF")
             (asset "PLTZ" "Defiance 2x Short PLTR ETF")
             (asset "CORD" "T-REX 2X Inverse CRWV Daily Target ETF")
             (asset
              "ORCS"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bear 1X ETF")
             (asset "RGTZ" "Defiance 2x Short RGTI ETF")
             (asset "IONZ" "Defiance 2x Short IONQ ETF")
             (asset "QBTZ" "Defiance 2x Short QBTS ETF")
             (asset "MSTZ" "T-Rex 2X Inverse MSTR Daily Target ETF")
             (asset "CONI" "GraniteShares 2x Short COIN Daily ETF")
             (asset "BITI" "ProShares Short Bitcoin ETF")
             (asset
              "SBIT"
              "ProShares Trust - ProShares UltraShort Bitcoin ETF")
             (asset "BTCZ" "T-Rex 2X Inverse Bitcoin Daily Target ETF")
             (asset "ETHD" "ProShares UltraShort Ether ETF")
             (asset "SOLZ" "Solana ETF")
             (asset "XRPZ" "Franklin XRP Trust")
             (asset "HOOZ" "Defiance 2X Short HOOD ETF")
             (asset "REKT" "Direxion Daily Crypto Industry Bear 1X")
             (asset "RKLZ" "Defiance 2x Short RKLB ETF")
             (asset "OKLS" "Defiance 2X Short OKLO ETF")
             (asset "ERY" "Direxion Daily Energy Bear -2X Shares")
             (asset "DRIP" "Direxion Daily S&P Oil & Gas Bear 2X")
             (asset "SCO" "ProShares UltraShort Bloomberg Crude Oil")
             (asset
              "KOLD"
              "ProShares UltraShort Bloomberg Natural Gas")
             (asset
              "GLL"
              "ProShares Trust - ProShares UltraShort Gold -2x Shares")
             (asset "DUST" "Direxion Daily Gold Miners Bear -2X")
             (asset "ZSL" "ProShares UltraShort Silver")
             (asset "LLYZ" "Defiance 2X Short LLY ETF")
             (asset
              "BITX"
              "Volatility Shares Trust - 2x Bitcoin Strategy ETF")
             (asset
              "AAPU"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bull 2X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "UTSL"
              "Direxion Shares ETF Trust - Direxion Daily Utilities Bull 3X Shares")
             (asset
              "DFEN"
              "Direxion Shares ETF Trust - Direxion Daily Aerospace & Defense Bull 3X Shares")
             (asset
              "LRCU"
              "Investment Managers Series Trust II - Tradr 2X Long LRCX Daily ETF")
             (asset
              "LABX"
              "Investment Managers Series Trust II - Tradr 2X Long ALAB Daily ETF")
             (asset
              "CRDU"
              "Investment Managers Series Trust II - Tradr 2X Long CRDO Daily ETF")
             (asset
              "CRCD"
              "ETF Opportunities Trust - T-REX 2X Inverse CRCL Daily Target ETF")
             (asset
              "DOGD"
              "Investment Managers Series Trust II - Tradr 2X Long DDOG Daily ETF")
             (asset
              "MDBX"
              "Investment Managers Series Trust II - Tradr 2X Long MDB Daily ETF")
             (asset
              "CLSX"
              "Investment Managers Series Trust II - Tradr 2X Long CLSK Daily ETF")
             (asset
              "COZX"
              "Investment Managers Series Trust II - Tradr 2X Long CORZ Daily ETF")
             (asset
              "CSEX"
              "Investment Managers Series Trust II - Tradr 2X Long CLS Daily ETF")
             (asset
              "JOBX"
              "Investment Managers Series Trust II - Tradr 2X Long JOBY Daily ETF")
             (asset
              "OPEX"
              "Investment Managers Series Trust II - Tradr 2X Long OPEN Daily ETF")
             (asset
              "WULX"
              "Investment Managers Series Trust II - Tradr 2X Long WULF Daily ETF")
             (asset
              "ANEL"
              "Tidal Trust II - Defiance Daily Target 2x Long ANET ETF")
             (asset
              "VSTL"
              "Tidal Trust II - Defiance Daily Target 2X Long VST ETF")
             (asset
              "SOUX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOUN ETF")
             (asset
              "RIOX"
              "Tidal Trust II - Defiance Daily Target 2X Long RIOT ETF")
             (asset
              "BU"
              "Tidal Trust II - Defiance Daily Target 2X Long BU ETF")
             (asset
              "SNOU"
              "ETF Opportunities Trust - T-REX 2X Long SNOW Daily Target ETF")
             (asset
              "DKUP"
              "ETF Opportunities Trust - T-REX 2X Long DKNG Daily Target ETF")
             (asset
              "AFRU"
              "ETF Opportunities Trust - T-REX 2X Long AFRM Daily Target ETF")
             (asset
              "KTUP"
              "Investment Managers Series Trust II - T-REX 2X Long KTOS Daily Target ETF")
             (asset
              "GLXU"
              "ETF Opportunities Trust - T-REX 2X Long GLXY Daily Target ETF")
             (asset
              "CCUP"
              "ETF Opportunities Trust - T-REX 2X Long CRCL Daily Target ETF")
             (asset
              "TSLQ"
              "Investment Managers Series Trust II - Tradr 2X Short TSLA Daily ETF")
             (asset
              "NVDS"
              "Investment Managers Series Trust II - Tradr 1.5X Short NVDA Daily ETF")
             (asset
              "SOFX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOFI ETF")
             (asset
              "MPL"
              "Tidal Trust II - Defiance Daily Target 2X Long MP ETF")
             (asset
              "CRMG"
              "Themes ETF Trust - Leverage Shares 2X Long CRM Daily ETF")
             (asset
              "ISUL"
              "GraniteShares ETF Trust - GraniteShares 2x Long ISRG Daily ETF")
             (asset
              "NOWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long NOW Daily ETF")
             (asset
              "PYPG"
              "Themes ETF Trust - Leverage Shares 2X Long PYPL Daily ETF")
             (asset
              "NFXS"
              "Direxion Shares ETF Trust - Direxion Daily NFLX Bear 1X Shares")
             (asset
              "BOED"
              "Direxion Shares ETF Trust - Direxion Daily BA Bear 1X Shares")
             (asset
              "LMTS"
              "Direxion Shares ETF Trust - Direxion Daily LMT Bear 1X ETF")
             (asset
              "XOMZ"
              "Direxion Shares ETF Trust - Direxion Daily XOM Bear 1X Shares")
             (asset
              "PALD"
              "Direxion Shares ETF Trust - Direxion Daily PANW Bear 1X Shares")
             (asset
              "AVS"
              "Direxion Shares ETF Trust - Direxion Daily AVGO Bear 1X Shares")
             (asset
              "QCMD"
              "Direxion Shares ETF Trust - Direxion Daily QCOM Bear 1X ETF")
             (asset
              "MUD"
              "Direxion Shares ETF Trust - Direxion Daily MU Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "CSCS"
              "Direxion Shares ETF Trust - Direxion Daily CSCO Bear 1X ETF")
             (asset
              "QQQD"
              "Direxion Shares ETF Trust - Direxion Daily Magnificent 7 Bear 1X Shares")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "BIL" "SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "LACG"
              "Themes ETF Trust - Leverage Shares 2X Long LAC Daily ETF")
             (asset
              "BEG"
              "Themes ETF Trust - Leverage Shares 2x Long BE Daily ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset
              "INDI"
              "Indie Semiconductor Inc - Ordinary Shares - Class A")
             (asset "GSIT" "GSI Technology Inc")
             (asset "SLS" "SELLAS Life Sciences Group Inc")
             (asset "SRFM" "Surf Air Mobility Inc")
             (asset
              "PXIU"
              "ETF Opportunities Trust - T-REX 2X Long UPXI Daily Target ETF")
             (asset "DRUG" "Bright Minds Biosciences Inc")
             (asset
              "CWEB"
              "Direxion Shares ETF Trust - Direxion Daily CSI China Internet Index Bull 2X Shares")
             (asset
              "XPP"
              "ProShares Trust - ProShares Ultra FTSE China 50 2x Shares")
             (asset
              "CHAU"
              "Direxion Shares ETF Trust - Direxion Daily CSI 300 China A Share Bull 2X Shares")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")])])
         (weight-equal
          [(filter
            (cumulative-return {:window 2})
            (select-top 3)
            [(asset "AMAT" "Applied Materials Inc.")
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
             (asset "WOLF" "Wolfspeed Inc")
             (asset "GLW" "Corning, Inc.")
             (asset "SNDK" "Sandisk Corp")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "AI" "C3.ai Inc")
             (asset "INOD" "Innodata Inc")
             (asset "QSI" "Quantum-Si Incorporated")
             (asset "DVLT" "Datavault AI Inc.")
             (asset "PATH" "UiPath Inc")
             (asset "CFLT" "Confluent Inc")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "DUOL" "Duolingo Inc")
             (asset "AMPL" "Amplitude Inc")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc")
             (asset "FTNT" "Fortinet Inc")
             (asset "RBRK" "Rubrik Inc.")
             (asset "IBM" "International Business Machines Corp.")
             (asset "APH" "Amphenol Corp")
             (asset "HPE" "Hewlett Packard Enterprise Co")
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
             (asset "XYZ" "Block Inc")
             (asset "BKKT" "Bakkt Holdings Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset "SATL" "Satellogic Inc")
             (asset "SIDU" "Sidus Space Inc")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "AIRO" "AIRO Group Holdings Inc.")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LHX" "L3Harris Technologies Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset "CACI" "Caci International Inc.")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "CCJ" "Cameco Corp")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Uranium ETF")
             (asset "URNJ" "Sprott Junior Uranium Miners ETF")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset "CWEN" "Clearway Energy Inc")
             (asset "AMRC" "Ameresco Inc.")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset "TAN" "Invesco Solar ETF")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "FCEL" "Fuelcell Energy Inc")
             (asset "BLDP" "Ballard Power Systems Inc.")
             (asset "GEVO" "Gevo Inc")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset "HYLN" "Hyliion Holdings Corporation")
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
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset "DNA" "Ginkgo Bioworks Holdings Inc")
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
             (asset "QNTM" "Quantum BioPharma Ltd.")
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
             (asset "OMDA" "Omada Health Inc.")
             (asset "DXCM" "Dexcom Inc")
             (asset "GHRS" "GH Research PLC")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset "BFLY" "Butterfly Network Inc")
             (asset "ALIT" "Alight Inc.")
             (asset "WELL" "Welltower Inc.")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset "TECK" "Teck Resources Ltd")
             (asset "USAR" "USA Rare Earth Inc.")
             (asset "UAMY" "United States Antimony Corp")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "LIT" "Global X Lithium & Battery Tech ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "NU" "Nu Holdings Ltd")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset "GRAB" "Grab Holdings Limited")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset "JCI" "Johnson Controls International plc")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "PRLB" "Proto Labs Inc")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "VMC" "Vulcan Materials Co")
             (asset "ASPN" "Aspen Aerogels Inc.")
             (asset "NNDM" "Nano Dimension Ltd - ADR")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "LPTH" "Lightpath Technologies, Inc.")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "KOPN" "Kopin Corp.")
             (asset "WYFI" "Whitefiber Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset "PSTL" "Postal Realty Trust Inc")
             (asset "CAVA" "Cava Group Inc")
             (asset "SMH" "VanEck Semiconductor ETF")
             (asset "SMHX" "VanEck Fabless Semiconductor ETF")
             (asset "XLK" "Technology Select Sector SPDR ETF")
             (asset "XLI" "Industrial Select Sector SPDR ETF")
             (asset "XME" "SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "ETH" "Grayscale Ethereum Mini Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset "NVDL" "GraniteShares 2x Long NVDA Daily ETF")
             (asset "MULL" "GraniteShares 2x Long MU Daily ETF")
             (asset "MVLL" "GraniteShares 2x Long MRVL Daily ETF")
             (asset "AMDU" "Defiance Leveraged Long + Income AMD ETF")
             (asset "TSLL" "Direxion Daily TSLA Bull 2X Shares")
             (asset "TSMU" "GraniteShares 2x Long TSM Daily ETF")
             (asset "SMCX" "Defiance 2x Long SMCI ETF")
             (asset
              "ARMG"
              "Themes ETF Trust - Leverage Shares 2X Long ARM Daily ETF")
             (asset
              "AVGU"
              "GraniteShares ETF Trust - GraniteShares 2x Long AVGO Daily ETF")
             (asset
              "INTW"
              "GraniteShares ETF Trust - GraniteShares 2x Long INTC Daily ETF")
             (asset
              "QCML"
              "GraniteShares ETF Trust - GraniteShares 2x Long QCOM Daily ETF")
             (asset "PTIR" "GraniteShares 2x Long PLTR Daily ETF")
             (asset "NEBX" "Tradr 2X Long NBIS Daily ETF")
             (asset "NETX" "Tradr 2X Long NET Daily ETF")
             (asset "CRWU" "T-REX 2X Long CRWV Daily Target ETF")
             (asset
              "SKYU"
              "ProShares Ultra Nasdaq Cloud Computing ETF")
             (asset "PALU" "Direxion Daily PANW Bull 2X Shares")
             (asset "UCYB" "ProShares Ultra Nasdaq Cybersecurity ETF")
             (asset "TEMT" "Tradr 2X Long TEM Daily ETF")
             (asset
              "APPX"
              "Investment Managers Series Trust II - Tradr 2X Long APP Daily ETF")
             (asset
              "CRWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long CRWD Daily ETF")
             (asset
              "UBOT"
              "Direxion Shares ETF Trust - Daily Robotics, Artificial Intelligence & Automation Index Bull 2X Shares")
             (asset
              "MSFL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MSFT Daily ETF")
             (asset
              "GOOX"
              "ETF Opportunities Trust - T-Rex 2X Long Alphabet Daily Target ETF")
             (asset
              "AMZZ"
              "GraniteShares ETF Trust - GraniteShares 2x Long AMZN Daily ETF")
             (asset
              "FBL"
              "GraniteShares ETF Trust - GraniteShares 2x Long META Daily ETF")
             (asset
              "DLLL"
              "GraniteShares ETF Trust - GraniteShares 2x Long DELL Daily ETF")
             (asset
              "RDTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RDDT Daily ETF")
             (asset
              "VRTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long VRT Daily ETF")
             (asset
              "ORCU"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bull 2X ETF")
             (asset "IONL" "GraniteShares 2x Long IONQ Daily ETF")
             (asset "RGTX" "Defiance 2X Long RGTI Daily ETF")
             (asset "QBTX" "Tradr 2X Long QBTS Daily ETF")
             (asset "QUBX" "Tradr 2X Long QUBT Daily ETF")
             (asset "QPUX" "Defiance 2X Long Pure Quantum ETF")
             (asset "MSTU" "T-Rex 2X Long MSTR Daily Target ETF")
             (asset "CONL" "GraniteShares 2x Long COIN Daily ETF")
             (asset "CIFU" "T-REX 2X Long CIFR Daily Target ETF")
             (asset "BTCL" "T-Rex 2X Long Bitcoin Daily Target ETF")
             (asset "ETHU" "2x Ether ETF")
             (asset "SOLT" "2x Solana ETF")
             (asset "XRPT" "XRP 2X ETF")
             (asset
              "XXRP"
              "Listed Funds Trust - Teucrium 2x Long Daily XRP ETF")
             (asset "HOOG" "Leverage Shares 2X Long HOOD Daily ETF")
             (asset
              "MRAL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MARA Daily ETF")
             (asset
              "BEGS"
              "Collaborative Investment Series Trust - Rareview 2x Bull Cryptocurrency & Precious Metals ETF")
             (asset "RKLX" "Defiance 2X Long RKLB ETF")
             (asset
              "ASTX"
              "Investment Managers Series Trust II - Tradr 2X Long ASTS Daily ETF")
             (asset "AVXX" "Defiance 2x Long AVAV ETF")
             (asset
              "BOEU"
              "Direxion Shares ETF Trust - Direxion Daily BA Bull 2X Shares")
             (asset
              "ARCX"
              "Investment Managers Series Trust II - Tradr 2X Long ACHR Daily ETF")
             (asset
              "PONX"
              "Investment Managers Series Trust II - Tradr 2X Long PONY Daily ETF")
             (asset "ENPX" "Tradr 2X Long ENPH Daily ETF")
             (asset "IREX" "Tradr 2X Long IREN Daily ETF")
             (asset "OKLL" "Defiance 2x Long OKLO ETF")
             (asset "NNEX" "Tradr 2X Long NNE Daily ETF")
             (asset
              "SMU"
              "Investment Managers Series Trust II - Tradr 2X Long SMR Daily ETF")
             (asset "BEX" "Tradr 2X Long BE Daily ETF")
             (asset "GEVX" "Tradr 2X Long GEV Daily ETF")
             (asset "QSX" "Tradr 2X Long QS Daily ETF")
             (asset
              "CEGX"
              "Investment Managers Series Trust II - Tradr 2X Long CEG Daily ETF")
             (asset "ERX" "Direxion Daily Energy Bull 2X Shares")
             (asset "GUSH" "Direxion Daily S&P Oil & Gas Bull 2X")
             (asset "UCO" "ProShares Ultra Bloomberg Crude Oil")
             (asset "BOIL" "ProShares Ultra Bloomberg Natural Gas")
             (asset "UGL" "ProShares Ultra Gold")
             (asset "NUGT" "Direxion Daily Gold Miners Bull 2X")
             (asset "JNUG" "Direxion Daily Junior Gold Miners Bull 2X")
             (asset "AGQ" "ProShares Ultra Silver")
             (asset "CPXR" "USCF Daily Target 2X Copper Index ETF")
             (asset "LLYX" "Defiance 2X Long LLY ETF")
             (asset
              "UNHG"
              "Themes ETF Trust - Leverage Shares 2X Long UNH Daily ETF")
             (asset
              "UPSX"
              "Investment Managers Series Trust II - Tradr 2X Long UPST Daily ETF")
             (asset
              "BABX"
              "GraniteShares ETF Trust - GraniteShares 2x Long BABA Daily ETF")
             (asset
              "PDDL"
              "GraniteShares ETF Trust - GraniteShares 2x Long PDD Daily ETF")
             (asset
              "RVNL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RIVN Daily ETF")
             (asset "NVDQ" "T-Rex 2X Inverse NVIDIA Daily Target ETF")
             (asset "DAMD" "Defiance 2X Short AMD ETF")
             (asset "STSM" "Defiance 2X Short TSM ETF")
             (asset "SMCZ" "Defiance 2X Short SMCI ETF")
             (asset "PLTZ" "Defiance 2x Short PLTR ETF")
             (asset "CORD" "T-REX 2X Inverse CRWV Daily Target ETF")
             (asset
              "ORCS"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bear 1X ETF")
             (asset "RGTZ" "Defiance 2x Short RGTI ETF")
             (asset "IONZ" "Defiance 2x Short IONQ ETF")
             (asset "QBTZ" "Defiance 2x Short QBTS ETF")
             (asset "MSTZ" "T-Rex 2X Inverse MSTR Daily Target ETF")
             (asset "CONI" "GraniteShares 2x Short COIN Daily ETF")
             (asset "BITI" "ProShares Short Bitcoin ETF")
             (asset
              "SBIT"
              "ProShares Trust - ProShares UltraShort Bitcoin ETF")
             (asset "BTCZ" "T-Rex 2X Inverse Bitcoin Daily Target ETF")
             (asset "ETHD" "ProShares UltraShort Ether ETF")
             (asset "SOLZ" "Solana ETF")
             (asset "XRPZ" "Franklin XRP Trust")
             (asset "HOOZ" "Defiance 2X Short HOOD ETF")
             (asset "REKT" "Direxion Daily Crypto Industry Bear 1X")
             (asset "RKLZ" "Defiance 2x Short RKLB ETF")
             (asset "OKLS" "Defiance 2X Short OKLO ETF")
             (asset "ERY" "Direxion Daily Energy Bear -2X Shares")
             (asset "DRIP" "Direxion Daily S&P Oil & Gas Bear 2X")
             (asset "SCO" "ProShares UltraShort Bloomberg Crude Oil")
             (asset
              "KOLD"
              "ProShares UltraShort Bloomberg Natural Gas")
             (asset
              "GLL"
              "ProShares Trust - ProShares UltraShort Gold -2x Shares")
             (asset "DUST" "Direxion Daily Gold Miners Bear -2X")
             (asset "ZSL" "ProShares UltraShort Silver")
             (asset "LLYZ" "Defiance 2X Short LLY ETF")
             (asset
              "BITX"
              "Volatility Shares Trust - 2x Bitcoin Strategy ETF")
             (asset
              "AAPU"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bull 2X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "UTSL"
              "Direxion Shares ETF Trust - Direxion Daily Utilities Bull 3X Shares")
             (asset
              "DFEN"
              "Direxion Shares ETF Trust - Direxion Daily Aerospace & Defense Bull 3X Shares")
             (asset
              "LRCU"
              "Investment Managers Series Trust II - Tradr 2X Long LRCX Daily ETF")
             (asset
              "LABX"
              "Investment Managers Series Trust II - Tradr 2X Long ALAB Daily ETF")
             (asset
              "CRDU"
              "Investment Managers Series Trust II - Tradr 2X Long CRDO Daily ETF")
             (asset
              "CRCD"
              "ETF Opportunities Trust - T-REX 2X Inverse CRCL Daily Target ETF")
             (asset
              "DOGD"
              "Investment Managers Series Trust II - Tradr 2X Long DDOG Daily ETF")
             (asset
              "MDBX"
              "Investment Managers Series Trust II - Tradr 2X Long MDB Daily ETF")
             (asset
              "CLSX"
              "Investment Managers Series Trust II - Tradr 2X Long CLSK Daily ETF")
             (asset
              "COZX"
              "Investment Managers Series Trust II - Tradr 2X Long CORZ Daily ETF")
             (asset
              "CSEX"
              "Investment Managers Series Trust II - Tradr 2X Long CLS Daily ETF")
             (asset
              "JOBX"
              "Investment Managers Series Trust II - Tradr 2X Long JOBY Daily ETF")
             (asset
              "OPEX"
              "Investment Managers Series Trust II - Tradr 2X Long OPEN Daily ETF")
             (asset
              "WULX"
              "Investment Managers Series Trust II - Tradr 2X Long WULF Daily ETF")
             (asset
              "ANEL"
              "Tidal Trust II - Defiance Daily Target 2x Long ANET ETF")
             (asset
              "VSTL"
              "Tidal Trust II - Defiance Daily Target 2X Long VST ETF")
             (asset
              "SOUX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOUN ETF")
             (asset
              "RIOX"
              "Tidal Trust II - Defiance Daily Target 2X Long RIOT ETF")
             (asset
              "BU"
              "Tidal Trust II - Defiance Daily Target 2X Long BU ETF")
             (asset
              "SNOU"
              "ETF Opportunities Trust - T-REX 2X Long SNOW Daily Target ETF")
             (asset
              "DKUP"
              "ETF Opportunities Trust - T-REX 2X Long DKNG Daily Target ETF")
             (asset
              "AFRU"
              "ETF Opportunities Trust - T-REX 2X Long AFRM Daily Target ETF")
             (asset
              "KTUP"
              "Investment Managers Series Trust II - T-REX 2X Long KTOS Daily Target ETF")
             (asset
              "GLXU"
              "ETF Opportunities Trust - T-REX 2X Long GLXY Daily Target ETF")
             (asset
              "CCUP"
              "ETF Opportunities Trust - T-REX 2X Long CRCL Daily Target ETF")
             (asset
              "TSLQ"
              "Investment Managers Series Trust II - Tradr 2X Short TSLA Daily ETF")
             (asset
              "NVDS"
              "Investment Managers Series Trust II - Tradr 1.5X Short NVDA Daily ETF")
             (asset
              "SOFX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOFI ETF")
             (asset
              "MPL"
              "Tidal Trust II - Defiance Daily Target 2X Long MP ETF")
             (asset
              "CRMG"
              "Themes ETF Trust - Leverage Shares 2X Long CRM Daily ETF")
             (asset
              "ISUL"
              "GraniteShares ETF Trust - GraniteShares 2x Long ISRG Daily ETF")
             (asset
              "NOWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long NOW Daily ETF")
             (asset
              "PYPG"
              "Themes ETF Trust - Leverage Shares 2X Long PYPL Daily ETF")
             (asset
              "NFXS"
              "Direxion Shares ETF Trust - Direxion Daily NFLX Bear 1X Shares")
             (asset
              "BOED"
              "Direxion Shares ETF Trust - Direxion Daily BA Bear 1X Shares")
             (asset
              "LMTS"
              "Direxion Shares ETF Trust - Direxion Daily LMT Bear 1X ETF")
             (asset
              "XOMZ"
              "Direxion Shares ETF Trust - Direxion Daily XOM Bear 1X Shares")
             (asset
              "PALD"
              "Direxion Shares ETF Trust - Direxion Daily PANW Bear 1X Shares")
             (asset
              "AVS"
              "Direxion Shares ETF Trust - Direxion Daily AVGO Bear 1X Shares")
             (asset
              "QCMD"
              "Direxion Shares ETF Trust - Direxion Daily QCOM Bear 1X ETF")
             (asset
              "MUD"
              "Direxion Shares ETF Trust - Direxion Daily MU Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "CSCS"
              "Direxion Shares ETF Trust - Direxion Daily CSCO Bear 1X ETF")
             (asset
              "QQQD"
              "Direxion Shares ETF Trust - Direxion Daily Magnificent 7 Bear 1X Shares")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "BIL" "SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "LACG"
              "Themes ETF Trust - Leverage Shares 2X Long LAC Daily ETF")
             (asset
              "BEG"
              "Themes ETF Trust - Leverage Shares 2x Long BE Daily ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset
              "INDI"
              "Indie Semiconductor Inc - Ordinary Shares - Class A")
             (asset "GSIT" "GSI Technology Inc")
             (asset "SLS" "SELLAS Life Sciences Group Inc")
             (asset "SRFM" "Surf Air Mobility Inc")
             (asset
              "PXIU"
              "ETF Opportunities Trust - T-REX 2X Long UPXI Daily Target ETF")
             (asset "DRUG" "Bright Minds Biosciences Inc")
             (asset
              "CWEB"
              "Direxion Shares ETF Trust - Direxion Daily CSI China Internet Index Bull 2X Shares")
             (asset
              "XPP"
              "ProShares Trust - ProShares Ultra FTSE China 50 2x Shares")
             (asset
              "CHAU"
              "Direxion Shares ETF Trust - Direxion Daily CSI 300 China A Share Bull 2X Shares")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")])])])
       (filter
        (rsi {:window 7})
        (select-bottom 2)
        [(weight-equal
          [(filter
            (cumulative-return {:window 2})
            (select-top 5)
            [(asset "AMAT" "Applied Materials Inc.")
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
             (asset "WOLF" "Wolfspeed Inc")
             (asset "GLW" "Corning, Inc.")
             (asset "SNDK" "Sandisk Corp")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "AI" "C3.ai Inc")
             (asset "INOD" "Innodata Inc")
             (asset "QSI" "Quantum-Si Incorporated")
             (asset "DVLT" "Datavault AI Inc.")
             (asset "PATH" "UiPath Inc")
             (asset "CFLT" "Confluent Inc")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "DUOL" "Duolingo Inc")
             (asset "AMPL" "Amplitude Inc")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc")
             (asset "FTNT" "Fortinet Inc")
             (asset "RBRK" "Rubrik Inc.")
             (asset "IBM" "International Business Machines Corp.")
             (asset "APH" "Amphenol Corp")
             (asset "HPE" "Hewlett Packard Enterprise Co")
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
             (asset "XYZ" "Block Inc")
             (asset "BKKT" "Bakkt Holdings Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset "SATL" "Satellogic Inc")
             (asset "SIDU" "Sidus Space Inc")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "AIRO" "AIRO Group Holdings Inc.")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LHX" "L3Harris Technologies Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset "CACI" "Caci International Inc.")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "CCJ" "Cameco Corp")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Uranium ETF")
             (asset "URNJ" "Sprott Junior Uranium Miners ETF")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset "CWEN" "Clearway Energy Inc")
             (asset "AMRC" "Ameresco Inc.")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset "TAN" "Invesco Solar ETF")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "FCEL" "Fuelcell Energy Inc")
             (asset "BLDP" "Ballard Power Systems Inc.")
             (asset "GEVO" "Gevo Inc")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset "HYLN" "Hyliion Holdings Corporation")
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
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset "DNA" "Ginkgo Bioworks Holdings Inc")
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
             (asset "QNTM" "Quantum BioPharma Ltd.")
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
             (asset "OMDA" "Omada Health Inc.")
             (asset "DXCM" "Dexcom Inc")
             (asset "GHRS" "GH Research PLC")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset "BFLY" "Butterfly Network Inc")
             (asset "ALIT" "Alight Inc.")
             (asset "WELL" "Welltower Inc.")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset "TECK" "Teck Resources Ltd")
             (asset "USAR" "USA Rare Earth Inc.")
             (asset "UAMY" "United States Antimony Corp")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "LIT" "Global X Lithium & Battery Tech ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "NU" "Nu Holdings Ltd")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset "GRAB" "Grab Holdings Limited")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset "JCI" "Johnson Controls International plc")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "PRLB" "Proto Labs Inc")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "VMC" "Vulcan Materials Co")
             (asset "ASPN" "Aspen Aerogels Inc.")
             (asset "NNDM" "Nano Dimension Ltd - ADR")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "LPTH" "Lightpath Technologies, Inc.")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "KOPN" "Kopin Corp.")
             (asset "WYFI" "Whitefiber Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset "PSTL" "Postal Realty Trust Inc")
             (asset "CAVA" "Cava Group Inc")
             (asset "SMH" "VanEck Semiconductor ETF")
             (asset "SMHX" "VanEck Fabless Semiconductor ETF")
             (asset "XLK" "Technology Select Sector SPDR ETF")
             (asset "XLI" "Industrial Select Sector SPDR ETF")
             (asset "XME" "SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "ETH" "Grayscale Ethereum Mini Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset "NVDL" "GraniteShares 2x Long NVDA Daily ETF")
             (asset "MULL" "GraniteShares 2x Long MU Daily ETF")
             (asset "MVLL" "GraniteShares 2x Long MRVL Daily ETF")
             (asset "AMDU" "Defiance Leveraged Long + Income AMD ETF")
             (asset "TSLL" "Direxion Daily TSLA Bull 2X Shares")
             (asset "TSMU" "GraniteShares 2x Long TSM Daily ETF")
             (asset "SMCX" "Defiance 2x Long SMCI ETF")
             (asset
              "ARMG"
              "Themes ETF Trust - Leverage Shares 2X Long ARM Daily ETF")
             (asset
              "AVGU"
              "GraniteShares ETF Trust - GraniteShares 2x Long AVGO Daily ETF")
             (asset
              "INTW"
              "GraniteShares ETF Trust - GraniteShares 2x Long INTC Daily ETF")
             (asset
              "QCML"
              "GraniteShares ETF Trust - GraniteShares 2x Long QCOM Daily ETF")
             (asset "PTIR" "GraniteShares 2x Long PLTR Daily ETF")
             (asset "NEBX" "Tradr 2X Long NBIS Daily ETF")
             (asset "NETX" "Tradr 2X Long NET Daily ETF")
             (asset "CRWU" "T-REX 2X Long CRWV Daily Target ETF")
             (asset
              "SKYU"
              "ProShares Ultra Nasdaq Cloud Computing ETF")
             (asset "PALU" "Direxion Daily PANW Bull 2X Shares")
             (asset "UCYB" "ProShares Ultra Nasdaq Cybersecurity ETF")
             (asset "TEMT" "Tradr 2X Long TEM Daily ETF")
             (asset
              "APPX"
              "Investment Managers Series Trust II - Tradr 2X Long APP Daily ETF")
             (asset
              "CRWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long CRWD Daily ETF")
             (asset
              "UBOT"
              "Direxion Shares ETF Trust - Daily Robotics, Artificial Intelligence & Automation Index Bull 2X Shares")
             (asset
              "MSFL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MSFT Daily ETF")
             (asset
              "GOOX"
              "ETF Opportunities Trust - T-Rex 2X Long Alphabet Daily Target ETF")
             (asset
              "AMZZ"
              "GraniteShares ETF Trust - GraniteShares 2x Long AMZN Daily ETF")
             (asset
              "FBL"
              "GraniteShares ETF Trust - GraniteShares 2x Long META Daily ETF")
             (asset
              "DLLL"
              "GraniteShares ETF Trust - GraniteShares 2x Long DELL Daily ETF")
             (asset
              "RDTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RDDT Daily ETF")
             (asset
              "VRTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long VRT Daily ETF")
             (asset
              "ORCU"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bull 2X ETF")
             (asset "IONL" "GraniteShares 2x Long IONQ Daily ETF")
             (asset "RGTX" "Defiance 2X Long RGTI Daily ETF")
             (asset "QBTX" "Tradr 2X Long QBTS Daily ETF")
             (asset "QUBX" "Tradr 2X Long QUBT Daily ETF")
             (asset "QPUX" "Defiance 2X Long Pure Quantum ETF")
             (asset "MSTU" "T-Rex 2X Long MSTR Daily Target ETF")
             (asset "CONL" "GraniteShares 2x Long COIN Daily ETF")
             (asset "CIFU" "T-REX 2X Long CIFR Daily Target ETF")
             (asset "BTCL" "T-Rex 2X Long Bitcoin Daily Target ETF")
             (asset "ETHU" "2x Ether ETF")
             (asset "SOLT" "2x Solana ETF")
             (asset "XRPT" "XRP 2X ETF")
             (asset
              "XXRP"
              "Listed Funds Trust - Teucrium 2x Long Daily XRP ETF")
             (asset "HOOG" "Leverage Shares 2X Long HOOD Daily ETF")
             (asset
              "MRAL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MARA Daily ETF")
             (asset
              "BEGS"
              "Collaborative Investment Series Trust - Rareview 2x Bull Cryptocurrency & Precious Metals ETF")
             (asset "RKLX" "Defiance 2X Long RKLB ETF")
             (asset
              "ASTX"
              "Investment Managers Series Trust II - Tradr 2X Long ASTS Daily ETF")
             (asset "AVXX" "Defiance 2x Long AVAV ETF")
             (asset
              "BOEU"
              "Direxion Shares ETF Trust - Direxion Daily BA Bull 2X Shares")
             (asset
              "ARCX"
              "Investment Managers Series Trust II - Tradr 2X Long ACHR Daily ETF")
             (asset
              "PONX"
              "Investment Managers Series Trust II - Tradr 2X Long PONY Daily ETF")
             (asset "ENPX" "Tradr 2X Long ENPH Daily ETF")
             (asset "IREX" "Tradr 2X Long IREN Daily ETF")
             (asset "OKLL" "Defiance 2x Long OKLO ETF")
             (asset "NNEX" "Tradr 2X Long NNE Daily ETF")
             (asset
              "SMU"
              "Investment Managers Series Trust II - Tradr 2X Long SMR Daily ETF")
             (asset "BEX" "Tradr 2X Long BE Daily ETF")
             (asset "GEVX" "Tradr 2X Long GEV Daily ETF")
             (asset "QSX" "Tradr 2X Long QS Daily ETF")
             (asset
              "CEGX"
              "Investment Managers Series Trust II - Tradr 2X Long CEG Daily ETF")
             (asset "ERX" "Direxion Daily Energy Bull 2X Shares")
             (asset "GUSH" "Direxion Daily S&P Oil & Gas Bull 2X")
             (asset "UCO" "ProShares Ultra Bloomberg Crude Oil")
             (asset "BOIL" "ProShares Ultra Bloomberg Natural Gas")
             (asset "UGL" "ProShares Ultra Gold")
             (asset "NUGT" "Direxion Daily Gold Miners Bull 2X")
             (asset "JNUG" "Direxion Daily Junior Gold Miners Bull 2X")
             (asset "AGQ" "ProShares Ultra Silver")
             (asset "CPXR" "USCF Daily Target 2X Copper Index ETF")
             (asset "LLYX" "Defiance 2X Long LLY ETF")
             (asset
              "UNHG"
              "Themes ETF Trust - Leverage Shares 2X Long UNH Daily ETF")
             (asset
              "UPSX"
              "Investment Managers Series Trust II - Tradr 2X Long UPST Daily ETF")
             (asset
              "BABX"
              "GraniteShares ETF Trust - GraniteShares 2x Long BABA Daily ETF")
             (asset
              "PDDL"
              "GraniteShares ETF Trust - GraniteShares 2x Long PDD Daily ETF")
             (asset
              "RVNL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RIVN Daily ETF")
             (asset "NVDQ" "T-Rex 2X Inverse NVIDIA Daily Target ETF")
             (asset "DAMD" "Defiance 2X Short AMD ETF")
             (asset "STSM" "Defiance 2X Short TSM ETF")
             (asset "SMCZ" "Defiance 2X Short SMCI ETF")
             (asset "PLTZ" "Defiance 2x Short PLTR ETF")
             (asset "CORD" "T-REX 2X Inverse CRWV Daily Target ETF")
             (asset
              "ORCS"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bear 1X ETF")
             (asset "RGTZ" "Defiance 2x Short RGTI ETF")
             (asset "IONZ" "Defiance 2x Short IONQ ETF")
             (asset "QBTZ" "Defiance 2x Short QBTS ETF")
             (asset "MSTZ" "T-Rex 2X Inverse MSTR Daily Target ETF")
             (asset "CONI" "GraniteShares 2x Short COIN Daily ETF")
             (asset "BITI" "ProShares Short Bitcoin ETF")
             (asset
              "SBIT"
              "ProShares Trust - ProShares UltraShort Bitcoin ETF")
             (asset "BTCZ" "T-Rex 2X Inverse Bitcoin Daily Target ETF")
             (asset "ETHD" "ProShares UltraShort Ether ETF")
             (asset "SOLZ" "Solana ETF")
             (asset "XRPZ" "Franklin XRP Trust")
             (asset "HOOZ" "Defiance 2X Short HOOD ETF")
             (asset "REKT" "Direxion Daily Crypto Industry Bear 1X")
             (asset "RKLZ" "Defiance 2x Short RKLB ETF")
             (asset "OKLS" "Defiance 2X Short OKLO ETF")
             (asset "ERY" "Direxion Daily Energy Bear -2X Shares")
             (asset "DRIP" "Direxion Daily S&P Oil & Gas Bear 2X")
             (asset "SCO" "ProShares UltraShort Bloomberg Crude Oil")
             (asset
              "KOLD"
              "ProShares UltraShort Bloomberg Natural Gas")
             (asset
              "GLL"
              "ProShares Trust - ProShares UltraShort Gold -2x Shares")
             (asset "DUST" "Direxion Daily Gold Miners Bear -2X")
             (asset "ZSL" "ProShares UltraShort Silver")
             (asset "LLYZ" "Defiance 2X Short LLY ETF")
             (asset
              "BITX"
              "Volatility Shares Trust - 2x Bitcoin Strategy ETF")
             (asset
              "AAPU"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bull 2X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "UTSL"
              "Direxion Shares ETF Trust - Direxion Daily Utilities Bull 3X Shares")
             (asset
              "DFEN"
              "Direxion Shares ETF Trust - Direxion Daily Aerospace & Defense Bull 3X Shares")
             (asset
              "LRCU"
              "Investment Managers Series Trust II - Tradr 2X Long LRCX Daily ETF")
             (asset
              "LABX"
              "Investment Managers Series Trust II - Tradr 2X Long ALAB Daily ETF")
             (asset
              "CRDU"
              "Investment Managers Series Trust II - Tradr 2X Long CRDO Daily ETF")
             (asset
              "CRCD"
              "ETF Opportunities Trust - T-REX 2X Inverse CRCL Daily Target ETF")
             (asset
              "DOGD"
              "Investment Managers Series Trust II - Tradr 2X Long DDOG Daily ETF")
             (asset
              "MDBX"
              "Investment Managers Series Trust II - Tradr 2X Long MDB Daily ETF")
             (asset
              "CLSX"
              "Investment Managers Series Trust II - Tradr 2X Long CLSK Daily ETF")
             (asset
              "COZX"
              "Investment Managers Series Trust II - Tradr 2X Long CORZ Daily ETF")
             (asset
              "CSEX"
              "Investment Managers Series Trust II - Tradr 2X Long CLS Daily ETF")
             (asset
              "JOBX"
              "Investment Managers Series Trust II - Tradr 2X Long JOBY Daily ETF")
             (asset
              "OPEX"
              "Investment Managers Series Trust II - Tradr 2X Long OPEN Daily ETF")
             (asset
              "WULX"
              "Investment Managers Series Trust II - Tradr 2X Long WULF Daily ETF")
             (asset
              "ANEL"
              "Tidal Trust II - Defiance Daily Target 2x Long ANET ETF")
             (asset
              "VSTL"
              "Tidal Trust II - Defiance Daily Target 2X Long VST ETF")
             (asset
              "SOUX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOUN ETF")
             (asset
              "RIOX"
              "Tidal Trust II - Defiance Daily Target 2X Long RIOT ETF")
             (asset
              "BU"
              "Tidal Trust II - Defiance Daily Target 2X Long BU ETF")
             (asset
              "SNOU"
              "ETF Opportunities Trust - T-REX 2X Long SNOW Daily Target ETF")
             (asset
              "DKUP"
              "ETF Opportunities Trust - T-REX 2X Long DKNG Daily Target ETF")
             (asset
              "AFRU"
              "ETF Opportunities Trust - T-REX 2X Long AFRM Daily Target ETF")
             (asset
              "KTUP"
              "Investment Managers Series Trust II - T-REX 2X Long KTOS Daily Target ETF")
             (asset
              "GLXU"
              "ETF Opportunities Trust - T-REX 2X Long GLXY Daily Target ETF")
             (asset
              "CCUP"
              "ETF Opportunities Trust - T-REX 2X Long CRCL Daily Target ETF")
             (asset
              "TSLQ"
              "Investment Managers Series Trust II - Tradr 2X Short TSLA Daily ETF")
             (asset
              "NVDS"
              "Investment Managers Series Trust II - Tradr 1.5X Short NVDA Daily ETF")
             (asset
              "SOFX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOFI ETF")
             (asset
              "MPL"
              "Tidal Trust II - Defiance Daily Target 2X Long MP ETF")
             (asset
              "CRMG"
              "Themes ETF Trust - Leverage Shares 2X Long CRM Daily ETF")
             (asset
              "ISUL"
              "GraniteShares ETF Trust - GraniteShares 2x Long ISRG Daily ETF")
             (asset
              "NOWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long NOW Daily ETF")
             (asset
              "PYPG"
              "Themes ETF Trust - Leverage Shares 2X Long PYPL Daily ETF")
             (asset
              "NFXS"
              "Direxion Shares ETF Trust - Direxion Daily NFLX Bear 1X Shares")
             (asset
              "BOED"
              "Direxion Shares ETF Trust - Direxion Daily BA Bear 1X Shares")
             (asset
              "LMTS"
              "Direxion Shares ETF Trust - Direxion Daily LMT Bear 1X ETF")
             (asset
              "XOMZ"
              "Direxion Shares ETF Trust - Direxion Daily XOM Bear 1X Shares")
             (asset
              "PALD"
              "Direxion Shares ETF Trust - Direxion Daily PANW Bear 1X Shares")
             (asset
              "AVS"
              "Direxion Shares ETF Trust - Direxion Daily AVGO Bear 1X Shares")
             (asset
              "QCMD"
              "Direxion Shares ETF Trust - Direxion Daily QCOM Bear 1X ETF")
             (asset
              "MUD"
              "Direxion Shares ETF Trust - Direxion Daily MU Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "CSCS"
              "Direxion Shares ETF Trust - Direxion Daily CSCO Bear 1X ETF")
             (asset
              "QQQD"
              "Direxion Shares ETF Trust - Direxion Daily Magnificent 7 Bear 1X Shares")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "BIL" "SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "LACG"
              "Themes ETF Trust - Leverage Shares 2X Long LAC Daily ETF")
             (asset
              "BEG"
              "Themes ETF Trust - Leverage Shares 2x Long BE Daily ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset
              "INDI"
              "Indie Semiconductor Inc - Ordinary Shares - Class A")
             (asset "GSIT" "GSI Technology Inc")
             (asset "SLS" "SELLAS Life Sciences Group Inc")
             (asset "SRFM" "Surf Air Mobility Inc")
             (asset
              "PXIU"
              "ETF Opportunities Trust - T-REX 2X Long UPXI Daily Target ETF")
             (asset "DRUG" "Bright Minds Biosciences Inc")
             (asset
              "CWEB"
              "Direxion Shares ETF Trust - Direxion Daily CSI China Internet Index Bull 2X Shares")
             (asset
              "XPP"
              "ProShares Trust - ProShares Ultra FTSE China 50 2x Shares")
             (asset
              "CHAU"
              "Direxion Shares ETF Trust - Direxion Daily CSI 300 China A Share Bull 2X Shares")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")])])
         (weight-equal
          [(filter
            (stdev-return {:window 2})
            (select-top 5)
            [(asset "AMAT" "Applied Materials Inc.")
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
             (asset "WOLF" "Wolfspeed Inc")
             (asset "GLW" "Corning, Inc.")
             (asset "SNDK" "Sandisk Corp")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "AI" "C3.ai Inc")
             (asset "INOD" "Innodata Inc")
             (asset "QSI" "Quantum-Si Incorporated")
             (asset "DVLT" "Datavault AI Inc.")
             (asset "PATH" "UiPath Inc")
             (asset "CFLT" "Confluent Inc")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "DUOL" "Duolingo Inc")
             (asset "AMPL" "Amplitude Inc")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc")
             (asset "FTNT" "Fortinet Inc")
             (asset "RBRK" "Rubrik Inc.")
             (asset "IBM" "International Business Machines Corp.")
             (asset "APH" "Amphenol Corp")
             (asset "HPE" "Hewlett Packard Enterprise Co")
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
             (asset "XYZ" "Block Inc")
             (asset "BKKT" "Bakkt Holdings Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset "SATL" "Satellogic Inc")
             (asset "SIDU" "Sidus Space Inc")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "AIRO" "AIRO Group Holdings Inc.")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LHX" "L3Harris Technologies Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset "CACI" "Caci International Inc.")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "CCJ" "Cameco Corp")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Uranium ETF")
             (asset "URNJ" "Sprott Junior Uranium Miners ETF")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset "CWEN" "Clearway Energy Inc")
             (asset "AMRC" "Ameresco Inc.")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset "TAN" "Invesco Solar ETF")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "FCEL" "Fuelcell Energy Inc")
             (asset "BLDP" "Ballard Power Systems Inc.")
             (asset "GEVO" "Gevo Inc")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset "HYLN" "Hyliion Holdings Corporation")
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
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset "DNA" "Ginkgo Bioworks Holdings Inc")
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
             (asset "QNTM" "Quantum BioPharma Ltd.")
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
             (asset "OMDA" "Omada Health Inc.")
             (asset "DXCM" "Dexcom Inc")
             (asset "GHRS" "GH Research PLC")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset "BFLY" "Butterfly Network Inc")
             (asset "ALIT" "Alight Inc.")
             (asset "WELL" "Welltower Inc.")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset "TECK" "Teck Resources Ltd")
             (asset "USAR" "USA Rare Earth Inc.")
             (asset "UAMY" "United States Antimony Corp")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "LIT" "Global X Lithium & Battery Tech ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "NU" "Nu Holdings Ltd")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset "GRAB" "Grab Holdings Limited")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset "JCI" "Johnson Controls International plc")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "PRLB" "Proto Labs Inc")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "VMC" "Vulcan Materials Co")
             (asset "ASPN" "Aspen Aerogels Inc.")
             (asset "NNDM" "Nano Dimension Ltd - ADR")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "LPTH" "Lightpath Technologies, Inc.")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "KOPN" "Kopin Corp.")
             (asset "WYFI" "Whitefiber Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset "PSTL" "Postal Realty Trust Inc")
             (asset "CAVA" "Cava Group Inc")
             (asset "SMH" "VanEck Semiconductor ETF")
             (asset "SMHX" "VanEck Fabless Semiconductor ETF")
             (asset "XLK" "Technology Select Sector SPDR ETF")
             (asset "XLI" "Industrial Select Sector SPDR ETF")
             (asset "XME" "SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "ETH" "Grayscale Ethereum Mini Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset "NVDL" "GraniteShares 2x Long NVDA Daily ETF")
             (asset "MULL" "GraniteShares 2x Long MU Daily ETF")
             (asset "MVLL" "GraniteShares 2x Long MRVL Daily ETF")
             (asset "AMDU" "Defiance Leveraged Long + Income AMD ETF")
             (asset "TSLL" "Direxion Daily TSLA Bull 2X Shares")
             (asset "TSMU" "GraniteShares 2x Long TSM Daily ETF")
             (asset "SMCX" "Defiance 2x Long SMCI ETF")
             (asset
              "ARMG"
              "Themes ETF Trust - Leverage Shares 2X Long ARM Daily ETF")
             (asset
              "AVGU"
              "GraniteShares ETF Trust - GraniteShares 2x Long AVGO Daily ETF")
             (asset
              "INTW"
              "GraniteShares ETF Trust - GraniteShares 2x Long INTC Daily ETF")
             (asset
              "QCML"
              "GraniteShares ETF Trust - GraniteShares 2x Long QCOM Daily ETF")
             (asset "PTIR" "GraniteShares 2x Long PLTR Daily ETF")
             (asset "NEBX" "Tradr 2X Long NBIS Daily ETF")
             (asset "NETX" "Tradr 2X Long NET Daily ETF")
             (asset "CRWU" "T-REX 2X Long CRWV Daily Target ETF")
             (asset
              "SKYU"
              "ProShares Ultra Nasdaq Cloud Computing ETF")
             (asset "PALU" "Direxion Daily PANW Bull 2X Shares")
             (asset "UCYB" "ProShares Ultra Nasdaq Cybersecurity ETF")
             (asset "TEMT" "Tradr 2X Long TEM Daily ETF")
             (asset
              "APPX"
              "Investment Managers Series Trust II - Tradr 2X Long APP Daily ETF")
             (asset
              "CRWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long CRWD Daily ETF")
             (asset
              "UBOT"
              "Direxion Shares ETF Trust - Daily Robotics, Artificial Intelligence & Automation Index Bull 2X Shares")
             (asset
              "MSFL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MSFT Daily ETF")
             (asset
              "GOOX"
              "ETF Opportunities Trust - T-Rex 2X Long Alphabet Daily Target ETF")
             (asset
              "AMZZ"
              "GraniteShares ETF Trust - GraniteShares 2x Long AMZN Daily ETF")
             (asset
              "FBL"
              "GraniteShares ETF Trust - GraniteShares 2x Long META Daily ETF")
             (asset
              "DLLL"
              "GraniteShares ETF Trust - GraniteShares 2x Long DELL Daily ETF")
             (asset
              "RDTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RDDT Daily ETF")
             (asset
              "VRTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long VRT Daily ETF")
             (asset
              "ORCU"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bull 2X ETF")
             (asset "IONL" "GraniteShares 2x Long IONQ Daily ETF")
             (asset "RGTX" "Defiance 2X Long RGTI Daily ETF")
             (asset "QBTX" "Tradr 2X Long QBTS Daily ETF")
             (asset "QUBX" "Tradr 2X Long QUBT Daily ETF")
             (asset "QPUX" "Defiance 2X Long Pure Quantum ETF")
             (asset "MSTU" "T-Rex 2X Long MSTR Daily Target ETF")
             (asset "CONL" "GraniteShares 2x Long COIN Daily ETF")
             (asset "CIFU" "T-REX 2X Long CIFR Daily Target ETF")
             (asset "BTCL" "T-Rex 2X Long Bitcoin Daily Target ETF")
             (asset "ETHU" "2x Ether ETF")
             (asset "SOLT" "2x Solana ETF")
             (asset "XRPT" "XRP 2X ETF")
             (asset
              "XXRP"
              "Listed Funds Trust - Teucrium 2x Long Daily XRP ETF")
             (asset "HOOG" "Leverage Shares 2X Long HOOD Daily ETF")
             (asset
              "MRAL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MARA Daily ETF")
             (asset
              "BEGS"
              "Collaborative Investment Series Trust - Rareview 2x Bull Cryptocurrency & Precious Metals ETF")
             (asset "RKLX" "Defiance 2X Long RKLB ETF")
             (asset
              "ASTX"
              "Investment Managers Series Trust II - Tradr 2X Long ASTS Daily ETF")
             (asset "AVXX" "Defiance 2x Long AVAV ETF")
             (asset
              "BOEU"
              "Direxion Shares ETF Trust - Direxion Daily BA Bull 2X Shares")
             (asset
              "ARCX"
              "Investment Managers Series Trust II - Tradr 2X Long ACHR Daily ETF")
             (asset
              "PONX"
              "Investment Managers Series Trust II - Tradr 2X Long PONY Daily ETF")
             (asset "ENPX" "Tradr 2X Long ENPH Daily ETF")
             (asset "IREX" "Tradr 2X Long IREN Daily ETF")
             (asset "OKLL" "Defiance 2x Long OKLO ETF")
             (asset "NNEX" "Tradr 2X Long NNE Daily ETF")
             (asset
              "SMU"
              "Investment Managers Series Trust II - Tradr 2X Long SMR Daily ETF")
             (asset "BEX" "Tradr 2X Long BE Daily ETF")
             (asset "GEVX" "Tradr 2X Long GEV Daily ETF")
             (asset "QSX" "Tradr 2X Long QS Daily ETF")
             (asset
              "CEGX"
              "Investment Managers Series Trust II - Tradr 2X Long CEG Daily ETF")
             (asset "ERX" "Direxion Daily Energy Bull 2X Shares")
             (asset "GUSH" "Direxion Daily S&P Oil & Gas Bull 2X")
             (asset "UCO" "ProShares Ultra Bloomberg Crude Oil")
             (asset "BOIL" "ProShares Ultra Bloomberg Natural Gas")
             (asset "UGL" "ProShares Ultra Gold")
             (asset "NUGT" "Direxion Daily Gold Miners Bull 2X")
             (asset "JNUG" "Direxion Daily Junior Gold Miners Bull 2X")
             (asset "AGQ" "ProShares Ultra Silver")
             (asset "CPXR" "USCF Daily Target 2X Copper Index ETF")
             (asset "LLYX" "Defiance 2X Long LLY ETF")
             (asset
              "UNHG"
              "Themes ETF Trust - Leverage Shares 2X Long UNH Daily ETF")
             (asset
              "UPSX"
              "Investment Managers Series Trust II - Tradr 2X Long UPST Daily ETF")
             (asset
              "BABX"
              "GraniteShares ETF Trust - GraniteShares 2x Long BABA Daily ETF")
             (asset
              "PDDL"
              "GraniteShares ETF Trust - GraniteShares 2x Long PDD Daily ETF")
             (asset
              "RVNL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RIVN Daily ETF")
             (asset "NVDQ" "T-Rex 2X Inverse NVIDIA Daily Target ETF")
             (asset "DAMD" "Defiance 2X Short AMD ETF")
             (asset "STSM" "Defiance 2X Short TSM ETF")
             (asset "SMCZ" "Defiance 2X Short SMCI ETF")
             (asset "PLTZ" "Defiance 2x Short PLTR ETF")
             (asset "CORD" "T-REX 2X Inverse CRWV Daily Target ETF")
             (asset
              "ORCS"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bear 1X ETF")
             (asset "RGTZ" "Defiance 2x Short RGTI ETF")
             (asset "IONZ" "Defiance 2x Short IONQ ETF")
             (asset "QBTZ" "Defiance 2x Short QBTS ETF")
             (asset "MSTZ" "T-Rex 2X Inverse MSTR Daily Target ETF")
             (asset "CONI" "GraniteShares 2x Short COIN Daily ETF")
             (asset "BITI" "ProShares Short Bitcoin ETF")
             (asset
              "SBIT"
              "ProShares Trust - ProShares UltraShort Bitcoin ETF")
             (asset "BTCZ" "T-Rex 2X Inverse Bitcoin Daily Target ETF")
             (asset "ETHD" "ProShares UltraShort Ether ETF")
             (asset "SOLZ" "Solana ETF")
             (asset "XRPZ" "Franklin XRP Trust")
             (asset "HOOZ" "Defiance 2X Short HOOD ETF")
             (asset "REKT" "Direxion Daily Crypto Industry Bear 1X")
             (asset "RKLZ" "Defiance 2x Short RKLB ETF")
             (asset "OKLS" "Defiance 2X Short OKLO ETF")
             (asset "ERY" "Direxion Daily Energy Bear -2X Shares")
             (asset "DRIP" "Direxion Daily S&P Oil & Gas Bear 2X")
             (asset "SCO" "ProShares UltraShort Bloomberg Crude Oil")
             (asset
              "KOLD"
              "ProShares UltraShort Bloomberg Natural Gas")
             (asset
              "GLL"
              "ProShares Trust - ProShares UltraShort Gold -2x Shares")
             (asset "DUST" "Direxion Daily Gold Miners Bear -2X")
             (asset "ZSL" "ProShares UltraShort Silver")
             (asset "LLYZ" "Defiance 2X Short LLY ETF")
             (asset
              "BITX"
              "Volatility Shares Trust - 2x Bitcoin Strategy ETF")
             (asset
              "AAPU"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bull 2X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "UTSL"
              "Direxion Shares ETF Trust - Direxion Daily Utilities Bull 3X Shares")
             (asset
              "DFEN"
              "Direxion Shares ETF Trust - Direxion Daily Aerospace & Defense Bull 3X Shares")
             (asset
              "LRCU"
              "Investment Managers Series Trust II - Tradr 2X Long LRCX Daily ETF")
             (asset
              "LABX"
              "Investment Managers Series Trust II - Tradr 2X Long ALAB Daily ETF")
             (asset
              "CRDU"
              "Investment Managers Series Trust II - Tradr 2X Long CRDO Daily ETF")
             (asset
              "CRCD"
              "ETF Opportunities Trust - T-REX 2X Inverse CRCL Daily Target ETF")
             (asset
              "DOGD"
              "Investment Managers Series Trust II - Tradr 2X Long DDOG Daily ETF")
             (asset
              "MDBX"
              "Investment Managers Series Trust II - Tradr 2X Long MDB Daily ETF")
             (asset
              "CLSX"
              "Investment Managers Series Trust II - Tradr 2X Long CLSK Daily ETF")
             (asset
              "COZX"
              "Investment Managers Series Trust II - Tradr 2X Long CORZ Daily ETF")
             (asset
              "CSEX"
              "Investment Managers Series Trust II - Tradr 2X Long CLS Daily ETF")
             (asset
              "JOBX"
              "Investment Managers Series Trust II - Tradr 2X Long JOBY Daily ETF")
             (asset
              "OPEX"
              "Investment Managers Series Trust II - Tradr 2X Long OPEN Daily ETF")
             (asset
              "WULX"
              "Investment Managers Series Trust II - Tradr 2X Long WULF Daily ETF")
             (asset
              "ANEL"
              "Tidal Trust II - Defiance Daily Target 2x Long ANET ETF")
             (asset
              "VSTL"
              "Tidal Trust II - Defiance Daily Target 2X Long VST ETF")
             (asset
              "SOUX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOUN ETF")
             (asset
              "RIOX"
              "Tidal Trust II - Defiance Daily Target 2X Long RIOT ETF")
             (asset
              "BU"
              "Tidal Trust II - Defiance Daily Target 2X Long BU ETF")
             (asset
              "SNOU"
              "ETF Opportunities Trust - T-REX 2X Long SNOW Daily Target ETF")
             (asset
              "DKUP"
              "ETF Opportunities Trust - T-REX 2X Long DKNG Daily Target ETF")
             (asset
              "AFRU"
              "ETF Opportunities Trust - T-REX 2X Long AFRM Daily Target ETF")
             (asset
              "KTUP"
              "Investment Managers Series Trust II - T-REX 2X Long KTOS Daily Target ETF")
             (asset
              "GLXU"
              "ETF Opportunities Trust - T-REX 2X Long GLXY Daily Target ETF")
             (asset
              "CCUP"
              "ETF Opportunities Trust - T-REX 2X Long CRCL Daily Target ETF")
             (asset
              "TSLQ"
              "Investment Managers Series Trust II - Tradr 2X Short TSLA Daily ETF")
             (asset
              "NVDS"
              "Investment Managers Series Trust II - Tradr 1.5X Short NVDA Daily ETF")
             (asset
              "SOFX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOFI ETF")
             (asset
              "MPL"
              "Tidal Trust II - Defiance Daily Target 2X Long MP ETF")
             (asset
              "CRMG"
              "Themes ETF Trust - Leverage Shares 2X Long CRM Daily ETF")
             (asset
              "ISUL"
              "GraniteShares ETF Trust - GraniteShares 2x Long ISRG Daily ETF")
             (asset
              "NOWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long NOW Daily ETF")
             (asset
              "PYPG"
              "Themes ETF Trust - Leverage Shares 2X Long PYPL Daily ETF")
             (asset
              "NFXS"
              "Direxion Shares ETF Trust - Direxion Daily NFLX Bear 1X Shares")
             (asset
              "BOED"
              "Direxion Shares ETF Trust - Direxion Daily BA Bear 1X Shares")
             (asset
              "LMTS"
              "Direxion Shares ETF Trust - Direxion Daily LMT Bear 1X ETF")
             (asset
              "XOMZ"
              "Direxion Shares ETF Trust - Direxion Daily XOM Bear 1X Shares")
             (asset
              "PALD"
              "Direxion Shares ETF Trust - Direxion Daily PANW Bear 1X Shares")
             (asset
              "AVS"
              "Direxion Shares ETF Trust - Direxion Daily AVGO Bear 1X Shares")
             (asset
              "QCMD"
              "Direxion Shares ETF Trust - Direxion Daily QCOM Bear 1X ETF")
             (asset
              "MUD"
              "Direxion Shares ETF Trust - Direxion Daily MU Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "CSCS"
              "Direxion Shares ETF Trust - Direxion Daily CSCO Bear 1X ETF")
             (asset
              "QQQD"
              "Direxion Shares ETF Trust - Direxion Daily Magnificent 7 Bear 1X Shares")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "BIL" "SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "LACG"
              "Themes ETF Trust - Leverage Shares 2X Long LAC Daily ETF")
             (asset
              "BEG"
              "Themes ETF Trust - Leverage Shares 2x Long BE Daily ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset
              "INDI"
              "Indie Semiconductor Inc - Ordinary Shares - Class A")
             (asset "GSIT" "GSI Technology Inc")
             (asset "SLS" "SELLAS Life Sciences Group Inc")
             (asset "SRFM" "Surf Air Mobility Inc")
             (asset
              "PXIU"
              "ETF Opportunities Trust - T-REX 2X Long UPXI Daily Target ETF")
             (asset "DRUG" "Bright Minds Biosciences Inc")
             (asset
              "CWEB"
              "Direxion Shares ETF Trust - Direxion Daily CSI China Internet Index Bull 2X Shares")
             (asset
              "XPP"
              "ProShares Trust - ProShares Ultra FTSE China 50 2x Shares")
             (asset
              "CHAU"
              "Direxion Shares ETF Trust - Direxion Daily CSI 300 China A Share Bull 2X Shares")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")])])
         (weight-equal
          [(filter
            (stdev-return {:window 2})
            (select-top 3)
            [(asset "AMAT" "Applied Materials Inc.")
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
             (asset "WOLF" "Wolfspeed Inc")
             (asset "GLW" "Corning, Inc.")
             (asset "SNDK" "Sandisk Corp")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "AI" "C3.ai Inc")
             (asset "INOD" "Innodata Inc")
             (asset "QSI" "Quantum-Si Incorporated")
             (asset "DVLT" "Datavault AI Inc.")
             (asset "PATH" "UiPath Inc")
             (asset "CFLT" "Confluent Inc")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "DUOL" "Duolingo Inc")
             (asset "AMPL" "Amplitude Inc")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc")
             (asset "FTNT" "Fortinet Inc")
             (asset "RBRK" "Rubrik Inc.")
             (asset "IBM" "International Business Machines Corp.")
             (asset "APH" "Amphenol Corp")
             (asset "HPE" "Hewlett Packard Enterprise Co")
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
             (asset "XYZ" "Block Inc")
             (asset "BKKT" "Bakkt Holdings Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset "SATL" "Satellogic Inc")
             (asset "SIDU" "Sidus Space Inc")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "AIRO" "AIRO Group Holdings Inc.")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LHX" "L3Harris Technologies Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset "CACI" "Caci International Inc.")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "CCJ" "Cameco Corp")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Uranium ETF")
             (asset "URNJ" "Sprott Junior Uranium Miners ETF")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset "CWEN" "Clearway Energy Inc")
             (asset "AMRC" "Ameresco Inc.")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset "TAN" "Invesco Solar ETF")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "FCEL" "Fuelcell Energy Inc")
             (asset "BLDP" "Ballard Power Systems Inc.")
             (asset "GEVO" "Gevo Inc")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset "HYLN" "Hyliion Holdings Corporation")
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
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset "DNA" "Ginkgo Bioworks Holdings Inc")
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
             (asset "QNTM" "Quantum BioPharma Ltd.")
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
             (asset "OMDA" "Omada Health Inc.")
             (asset "DXCM" "Dexcom Inc")
             (asset "GHRS" "GH Research PLC")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset "BFLY" "Butterfly Network Inc")
             (asset "ALIT" "Alight Inc.")
             (asset "WELL" "Welltower Inc.")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset "TECK" "Teck Resources Ltd")
             (asset "USAR" "USA Rare Earth Inc.")
             (asset "UAMY" "United States Antimony Corp")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "LIT" "Global X Lithium & Battery Tech ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "NU" "Nu Holdings Ltd")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset "GRAB" "Grab Holdings Limited")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset "JCI" "Johnson Controls International plc")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "PRLB" "Proto Labs Inc")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "VMC" "Vulcan Materials Co")
             (asset "ASPN" "Aspen Aerogels Inc.")
             (asset "NNDM" "Nano Dimension Ltd - ADR")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "LPTH" "Lightpath Technologies, Inc.")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "KOPN" "Kopin Corp.")
             (asset "WYFI" "Whitefiber Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset "PSTL" "Postal Realty Trust Inc")
             (asset "CAVA" "Cava Group Inc")
             (asset "SMH" "VanEck Semiconductor ETF")
             (asset "SMHX" "VanEck Fabless Semiconductor ETF")
             (asset "XLK" "Technology Select Sector SPDR ETF")
             (asset "XLI" "Industrial Select Sector SPDR ETF")
             (asset "XME" "SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "ETH" "Grayscale Ethereum Mini Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset "NVDL" "GraniteShares 2x Long NVDA Daily ETF")
             (asset "MULL" "GraniteShares 2x Long MU Daily ETF")
             (asset "MVLL" "GraniteShares 2x Long MRVL Daily ETF")
             (asset "AMDU" "Defiance Leveraged Long + Income AMD ETF")
             (asset "TSLL" "Direxion Daily TSLA Bull 2X Shares")
             (asset "TSMU" "GraniteShares 2x Long TSM Daily ETF")
             (asset "SMCX" "Defiance 2x Long SMCI ETF")
             (asset
              "ARMG"
              "Themes ETF Trust - Leverage Shares 2X Long ARM Daily ETF")
             (asset
              "AVGU"
              "GraniteShares ETF Trust - GraniteShares 2x Long AVGO Daily ETF")
             (asset
              "INTW"
              "GraniteShares ETF Trust - GraniteShares 2x Long INTC Daily ETF")
             (asset
              "QCML"
              "GraniteShares ETF Trust - GraniteShares 2x Long QCOM Daily ETF")
             (asset "PTIR" "GraniteShares 2x Long PLTR Daily ETF")
             (asset "NEBX" "Tradr 2X Long NBIS Daily ETF")
             (asset "NETX" "Tradr 2X Long NET Daily ETF")
             (asset "CRWU" "T-REX 2X Long CRWV Daily Target ETF")
             (asset
              "SKYU"
              "ProShares Ultra Nasdaq Cloud Computing ETF")
             (asset "PALU" "Direxion Daily PANW Bull 2X Shares")
             (asset "UCYB" "ProShares Ultra Nasdaq Cybersecurity ETF")
             (asset "TEMT" "Tradr 2X Long TEM Daily ETF")
             (asset
              "APPX"
              "Investment Managers Series Trust II - Tradr 2X Long APP Daily ETF")
             (asset
              "CRWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long CRWD Daily ETF")
             (asset
              "UBOT"
              "Direxion Shares ETF Trust - Daily Robotics, Artificial Intelligence & Automation Index Bull 2X Shares")
             (asset
              "MSFL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MSFT Daily ETF")
             (asset
              "GOOX"
              "ETF Opportunities Trust - T-Rex 2X Long Alphabet Daily Target ETF")
             (asset
              "AMZZ"
              "GraniteShares ETF Trust - GraniteShares 2x Long AMZN Daily ETF")
             (asset
              "FBL"
              "GraniteShares ETF Trust - GraniteShares 2x Long META Daily ETF")
             (asset
              "DLLL"
              "GraniteShares ETF Trust - GraniteShares 2x Long DELL Daily ETF")
             (asset
              "RDTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RDDT Daily ETF")
             (asset
              "VRTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long VRT Daily ETF")
             (asset
              "ORCU"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bull 2X ETF")
             (asset "IONL" "GraniteShares 2x Long IONQ Daily ETF")
             (asset "RGTX" "Defiance 2X Long RGTI Daily ETF")
             (asset "QBTX" "Tradr 2X Long QBTS Daily ETF")
             (asset "QUBX" "Tradr 2X Long QUBT Daily ETF")
             (asset "QPUX" "Defiance 2X Long Pure Quantum ETF")
             (asset "MSTU" "T-Rex 2X Long MSTR Daily Target ETF")
             (asset "CONL" "GraniteShares 2x Long COIN Daily ETF")
             (asset "CIFU" "T-REX 2X Long CIFR Daily Target ETF")
             (asset "BTCL" "T-Rex 2X Long Bitcoin Daily Target ETF")
             (asset "ETHU" "2x Ether ETF")
             (asset "SOLT" "2x Solana ETF")
             (asset "XRPT" "XRP 2X ETF")
             (asset
              "XXRP"
              "Listed Funds Trust - Teucrium 2x Long Daily XRP ETF")
             (asset "HOOG" "Leverage Shares 2X Long HOOD Daily ETF")
             (asset
              "MRAL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MARA Daily ETF")
             (asset
              "BEGS"
              "Collaborative Investment Series Trust - Rareview 2x Bull Cryptocurrency & Precious Metals ETF")
             (asset "RKLX" "Defiance 2X Long RKLB ETF")
             (asset
              "ASTX"
              "Investment Managers Series Trust II - Tradr 2X Long ASTS Daily ETF")
             (asset "AVXX" "Defiance 2x Long AVAV ETF")
             (asset
              "BOEU"
              "Direxion Shares ETF Trust - Direxion Daily BA Bull 2X Shares")
             (asset
              "ARCX"
              "Investment Managers Series Trust II - Tradr 2X Long ACHR Daily ETF")
             (asset
              "PONX"
              "Investment Managers Series Trust II - Tradr 2X Long PONY Daily ETF")
             (asset "ENPX" "Tradr 2X Long ENPH Daily ETF")
             (asset "IREX" "Tradr 2X Long IREN Daily ETF")
             (asset "OKLL" "Defiance 2x Long OKLO ETF")
             (asset "NNEX" "Tradr 2X Long NNE Daily ETF")
             (asset
              "SMU"
              "Investment Managers Series Trust II - Tradr 2X Long SMR Daily ETF")
             (asset "BEX" "Tradr 2X Long BE Daily ETF")
             (asset "GEVX" "Tradr 2X Long GEV Daily ETF")
             (asset "QSX" "Tradr 2X Long QS Daily ETF")
             (asset
              "CEGX"
              "Investment Managers Series Trust II - Tradr 2X Long CEG Daily ETF")
             (asset "ERX" "Direxion Daily Energy Bull 2X Shares")
             (asset "GUSH" "Direxion Daily S&P Oil & Gas Bull 2X")
             (asset "UCO" "ProShares Ultra Bloomberg Crude Oil")
             (asset "BOIL" "ProShares Ultra Bloomberg Natural Gas")
             (asset "UGL" "ProShares Ultra Gold")
             (asset "NUGT" "Direxion Daily Gold Miners Bull 2X")
             (asset "JNUG" "Direxion Daily Junior Gold Miners Bull 2X")
             (asset "AGQ" "ProShares Ultra Silver")
             (asset "CPXR" "USCF Daily Target 2X Copper Index ETF")
             (asset "LLYX" "Defiance 2X Long LLY ETF")
             (asset
              "UNHG"
              "Themes ETF Trust - Leverage Shares 2X Long UNH Daily ETF")
             (asset
              "UPSX"
              "Investment Managers Series Trust II - Tradr 2X Long UPST Daily ETF")
             (asset
              "BABX"
              "GraniteShares ETF Trust - GraniteShares 2x Long BABA Daily ETF")
             (asset
              "PDDL"
              "GraniteShares ETF Trust - GraniteShares 2x Long PDD Daily ETF")
             (asset
              "RVNL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RIVN Daily ETF")
             (asset "NVDQ" "T-Rex 2X Inverse NVIDIA Daily Target ETF")
             (asset "DAMD" "Defiance 2X Short AMD ETF")
             (asset "STSM" "Defiance 2X Short TSM ETF")
             (asset "SMCZ" "Defiance 2X Short SMCI ETF")
             (asset "PLTZ" "Defiance 2x Short PLTR ETF")
             (asset "CORD" "T-REX 2X Inverse CRWV Daily Target ETF")
             (asset
              "ORCS"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bear 1X ETF")
             (asset "RGTZ" "Defiance 2x Short RGTI ETF")
             (asset "IONZ" "Defiance 2x Short IONQ ETF")
             (asset "QBTZ" "Defiance 2x Short QBTS ETF")
             (asset "MSTZ" "T-Rex 2X Inverse MSTR Daily Target ETF")
             (asset "CONI" "GraniteShares 2x Short COIN Daily ETF")
             (asset "BITI" "ProShares Short Bitcoin ETF")
             (asset
              "SBIT"
              "ProShares Trust - ProShares UltraShort Bitcoin ETF")
             (asset "BTCZ" "T-Rex 2X Inverse Bitcoin Daily Target ETF")
             (asset "ETHD" "ProShares UltraShort Ether ETF")
             (asset "SOLZ" "Solana ETF")
             (asset "XRPZ" "Franklin XRP Trust")
             (asset "HOOZ" "Defiance 2X Short HOOD ETF")
             (asset "REKT" "Direxion Daily Crypto Industry Bear 1X")
             (asset "RKLZ" "Defiance 2x Short RKLB ETF")
             (asset "OKLS" "Defiance 2X Short OKLO ETF")
             (asset "ERY" "Direxion Daily Energy Bear -2X Shares")
             (asset "DRIP" "Direxion Daily S&P Oil & Gas Bear 2X")
             (asset "SCO" "ProShares UltraShort Bloomberg Crude Oil")
             (asset
              "KOLD"
              "ProShares UltraShort Bloomberg Natural Gas")
             (asset
              "GLL"
              "ProShares Trust - ProShares UltraShort Gold -2x Shares")
             (asset "DUST" "Direxion Daily Gold Miners Bear -2X")
             (asset "ZSL" "ProShares UltraShort Silver")
             (asset "LLYZ" "Defiance 2X Short LLY ETF")
             (asset
              "BITX"
              "Volatility Shares Trust - 2x Bitcoin Strategy ETF")
             (asset
              "AAPU"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bull 2X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "UTSL"
              "Direxion Shares ETF Trust - Direxion Daily Utilities Bull 3X Shares")
             (asset
              "DFEN"
              "Direxion Shares ETF Trust - Direxion Daily Aerospace & Defense Bull 3X Shares")
             (asset
              "LRCU"
              "Investment Managers Series Trust II - Tradr 2X Long LRCX Daily ETF")
             (asset
              "LABX"
              "Investment Managers Series Trust II - Tradr 2X Long ALAB Daily ETF")
             (asset
              "CRDU"
              "Investment Managers Series Trust II - Tradr 2X Long CRDO Daily ETF")
             (asset
              "CRCD"
              "ETF Opportunities Trust - T-REX 2X Inverse CRCL Daily Target ETF")
             (asset
              "DOGD"
              "Investment Managers Series Trust II - Tradr 2X Long DDOG Daily ETF")
             (asset
              "MDBX"
              "Investment Managers Series Trust II - Tradr 2X Long MDB Daily ETF")
             (asset
              "CLSX"
              "Investment Managers Series Trust II - Tradr 2X Long CLSK Daily ETF")
             (asset
              "COZX"
              "Investment Managers Series Trust II - Tradr 2X Long CORZ Daily ETF")
             (asset
              "CSEX"
              "Investment Managers Series Trust II - Tradr 2X Long CLS Daily ETF")
             (asset
              "JOBX"
              "Investment Managers Series Trust II - Tradr 2X Long JOBY Daily ETF")
             (asset
              "OPEX"
              "Investment Managers Series Trust II - Tradr 2X Long OPEN Daily ETF")
             (asset
              "WULX"
              "Investment Managers Series Trust II - Tradr 2X Long WULF Daily ETF")
             (asset
              "ANEL"
              "Tidal Trust II - Defiance Daily Target 2x Long ANET ETF")
             (asset
              "VSTL"
              "Tidal Trust II - Defiance Daily Target 2X Long VST ETF")
             (asset
              "SOUX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOUN ETF")
             (asset
              "RIOX"
              "Tidal Trust II - Defiance Daily Target 2X Long RIOT ETF")
             (asset
              "BU"
              "Tidal Trust II - Defiance Daily Target 2X Long BU ETF")
             (asset
              "SNOU"
              "ETF Opportunities Trust - T-REX 2X Long SNOW Daily Target ETF")
             (asset
              "DKUP"
              "ETF Opportunities Trust - T-REX 2X Long DKNG Daily Target ETF")
             (asset
              "AFRU"
              "ETF Opportunities Trust - T-REX 2X Long AFRM Daily Target ETF")
             (asset
              "KTUP"
              "Investment Managers Series Trust II - T-REX 2X Long KTOS Daily Target ETF")
             (asset
              "GLXU"
              "ETF Opportunities Trust - T-REX 2X Long GLXY Daily Target ETF")
             (asset
              "CCUP"
              "ETF Opportunities Trust - T-REX 2X Long CRCL Daily Target ETF")
             (asset
              "TSLQ"
              "Investment Managers Series Trust II - Tradr 2X Short TSLA Daily ETF")
             (asset
              "NVDS"
              "Investment Managers Series Trust II - Tradr 1.5X Short NVDA Daily ETF")
             (asset
              "SOFX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOFI ETF")
             (asset
              "MPL"
              "Tidal Trust II - Defiance Daily Target 2X Long MP ETF")
             (asset
              "CRMG"
              "Themes ETF Trust - Leverage Shares 2X Long CRM Daily ETF")
             (asset
              "ISUL"
              "GraniteShares ETF Trust - GraniteShares 2x Long ISRG Daily ETF")
             (asset
              "NOWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long NOW Daily ETF")
             (asset
              "PYPG"
              "Themes ETF Trust - Leverage Shares 2X Long PYPL Daily ETF")
             (asset
              "NFXS"
              "Direxion Shares ETF Trust - Direxion Daily NFLX Bear 1X Shares")
             (asset
              "BOED"
              "Direxion Shares ETF Trust - Direxion Daily BA Bear 1X Shares")
             (asset
              "LMTS"
              "Direxion Shares ETF Trust - Direxion Daily LMT Bear 1X ETF")
             (asset
              "XOMZ"
              "Direxion Shares ETF Trust - Direxion Daily XOM Bear 1X Shares")
             (asset
              "PALD"
              "Direxion Shares ETF Trust - Direxion Daily PANW Bear 1X Shares")
             (asset
              "AVS"
              "Direxion Shares ETF Trust - Direxion Daily AVGO Bear 1X Shares")
             (asset
              "QCMD"
              "Direxion Shares ETF Trust - Direxion Daily QCOM Bear 1X ETF")
             (asset
              "MUD"
              "Direxion Shares ETF Trust - Direxion Daily MU Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "CSCS"
              "Direxion Shares ETF Trust - Direxion Daily CSCO Bear 1X ETF")
             (asset
              "QQQD"
              "Direxion Shares ETF Trust - Direxion Daily Magnificent 7 Bear 1X Shares")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "BIL" "SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "LACG"
              "Themes ETF Trust - Leverage Shares 2X Long LAC Daily ETF")
             (asset
              "BEG"
              "Themes ETF Trust - Leverage Shares 2x Long BE Daily ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset
              "INDI"
              "Indie Semiconductor Inc - Ordinary Shares - Class A")
             (asset "GSIT" "GSI Technology Inc")
             (asset "SLS" "SELLAS Life Sciences Group Inc")
             (asset "SRFM" "Surf Air Mobility Inc")
             (asset
              "PXIU"
              "ETF Opportunities Trust - T-REX 2X Long UPXI Daily Target ETF")
             (asset "DRUG" "Bright Minds Biosciences Inc")
             (asset
              "CWEB"
              "Direxion Shares ETF Trust - Direxion Daily CSI China Internet Index Bull 2X Shares")
             (asset
              "XPP"
              "ProShares Trust - ProShares Ultra FTSE China 50 2x Shares")
             (asset
              "CHAU"
              "Direxion Shares ETF Trust - Direxion Daily CSI 300 China A Share Bull 2X Shares")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")])])
         (weight-equal
          [(filter
            (cumulative-return {:window 2})
            (select-top 3)
            [(asset "AMAT" "Applied Materials Inc.")
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
             (asset "WOLF" "Wolfspeed Inc")
             (asset "GLW" "Corning, Inc.")
             (asset "SNDK" "Sandisk Corp")
             (asset "ASML" "ASML Holding NV - New York Shares")
             (asset "COHR" "Coherent Corp")
             (asset "LITE" "Lumentum Holdings Inc")
             (asset "FORM" "FormFactor Inc.")
             (asset "KEYS" "Keysight Technologies Inc")
             (asset "ACLS" "Axcelis Technologies Inc")
             (asset "UCTT" "Ultra Clean Hldgs Inc")
             (asset "MKSI" "MKS Inc.")
             (asset "ARQQ" "Arqit Quantum Inc")
             (asset "BTQ" "BTQ Technologies Corp")
             (asset "BBAI" "BigBear.ai Holdings Inc")
             (asset "AI" "C3.ai Inc")
             (asset "INOD" "Innodata Inc")
             (asset "QSI" "Quantum-Si Incorporated")
             (asset "DVLT" "Datavault AI Inc.")
             (asset "PATH" "UiPath Inc")
             (asset "CFLT" "Confluent Inc")
             (asset "VEEV" "Veeva Systems Inc")
             (asset "HUBS" "HubSpot Inc")
             (asset "MNDY" "Monday.Com Ltd")
             (asset "DUOL" "Duolingo Inc")
             (asset "AMPL" "Amplitude Inc")
             (asset "DAVA" "Endava plc - ADR")
             (asset "SDGR" "Schrodinger Inc")
             (asset "ZS" "Zscaler Inc")
             (asset "S" "SentinelOne Inc")
             (asset "FTNT" "Fortinet Inc")
             (asset "RBRK" "Rubrik Inc.")
             (asset "IBM" "International Business Machines Corp.")
             (asset "APH" "Amphenol Corp")
             (asset "HPE" "Hewlett Packard Enterprise Co")
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
             (asset "XYZ" "Block Inc")
             (asset "BKKT" "Bakkt Holdings Inc")
             (asset "HUT" "Hut 8 Corp")
             (asset "BITF" "Bitfarms Ltd.")
             (asset "BTDR" "Bitdeer Technologies Group")
             (asset "APLD" "Applied Digital Corporation")
             (asset "BTBT" "Bit Digital Inc")
             (asset "LUNR" "Intuitive Machines Inc")
             (asset "SPCE" "Virgin Galactic Holdings Inc")
             (asset "RDW" "Redwire Corp")
             (asset "BKSY" "BlackSky Technology Inc")
             (asset "PL" "Planet Labs PBC")
             (asset "SPIR" "Spire Global Inc")
             (asset "IRDM" "Iridium Communications Inc")
             (asset "SATL" "Satellogic Inc")
             (asset "SIDU" "Sidus Space Inc")
             (asset "GILT" "Gilat Satellite Networks")
             (asset "VSAT" "Viasat, Inc.")
             (asset "EVEX" "Eve Holding Inc")
             (asset "EH" "EHang Holdings Ltd - ADR")
             (asset "AIRO" "AIRO Group Holdings Inc.")
             (asset "RCAT" "Red Cat Holdings Inc")
             (asset "UMAC" "Unusual Machines Inc")
             (asset "LMT" "Lockheed Martin Corp.")
             (asset "NOC" "Northrop Grumman Corp.")
             (asset "GD" "General Dynamics Corp.")
             (asset "RTX" "RTX Corp")
             (asset "HII" "Huntington Ingalls Industries Inc")
             (asset "LHX" "L3Harris Technologies Inc")
             (asset "LDOS" "Leidos Holdings Inc")
             (asset "CACI" "Caci International Inc.")
             (asset "BWXT" "BWX Technologies Inc")
             (asset "MRCY" "Mercury Systems Inc")
             (asset "ONDS" "Ondas Holdings Inc")
             (asset "SYM" "Symbotic Inc")
             (asset "TER" "Teradyne, Inc.")
             (asset "SERV" "Serve Robotics Inc")
             (asset "RR" "Richtech Robotics Inc.")
             (asset "OUST" "Ouster Inc")
             (asset "MBLY" "Mobileye Global Inc")
             (asset "AUR" "Aurora Innovation Inc")
             (asset "AMBA" "Ambarella Inc")
             (asset "PTC" "PTC Inc")
             (asset "CCJ" "Cameco Corp")
             (asset "LEU" "Centrus Energy Corp")
             (asset "UUUU" "Energy Fuels Inc")
             (asset "UEC" "Uranium Energy Corp")
             (asset "NXE" "NexGen Energy Ltd")
             (asset "DNN" "Denison Mines Corp")
             (asset "LTBR" "Lightbridge Corp")
             (asset "URA" "Global X Uranium ETF")
             (asset "URNJ" "Sprott Junior Uranium Miners ETF")
             (asset "FSLR" "First Solar Inc")
             (asset "SEDG" "SolarEdge Technologies Inc")
             (asset "ARRY" "Array Technologies Inc")
             (asset "NXT" "Nextracker Inc")
             (asset "MAXN" "Maxeon Solar Technologies Ltd")
             (asset "ORA" "Ormat Technologies Inc")
             (asset "CWEN" "Clearway Energy Inc")
             (asset "AMRC" "Ameresco Inc.")
             (asset "ELLO" "Ellomay Capital Ltd")
             (asset "VVPR" "VivoPower International PLC")
             (asset "TAN" "Invesco Solar ETF")
             (asset
              "BEPC"
              "Brookfield Renewable Corp. - Ordinary Shares - Class A (Exchangeable Sub Voting)")
             (asset "CSIQ" "Canadian Solar Inc")
             (asset
              "SHLS"
              "Shoals Technologies Group Inc - Ordinary Shares - Class A")
             (asset "JKS" "JinkoSolar Holding Co. Ltd - ADR")
             (asset "PLUG" "Plug Power Inc")
             (asset "FCEL" "Fuelcell Energy Inc")
             (asset "BLDP" "Ballard Power Systems Inc.")
             (asset "GEVO" "Gevo Inc")
             (asset "ENVX" "Enovix Corporation")
             (asset "AMPX" "Amprius Technologies Inc")
             (asset "FLNC" "Fluence Energy Inc")
             (asset "EOSE" "Eos Energy Enterprises Inc")
             (asset "NRGV" "Energy Vault Holdings Inc")
             (asset "ERII" "Energy Recovery Inc")
             (asset "MVST" "Microvast Holdings Inc")
             (asset "ENS" "Enersys")
             (asset "HYLN" "Hyliion Holdings Corporation")
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
             (asset "CRSP" "CRISPR Therapeutics AG")
             (asset "NTLA" "Intellia Therapeutics Inc")
             (asset "BEAM" "Beam Therapeutics Inc")
             (asset "EDIT" "Editas Medicine Inc")
             (asset "TWST" "Twist Bioscience Corp")
             (asset "DNA" "Ginkgo Bioworks Holdings Inc")
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
             (asset "QNTM" "Quantum BioPharma Ltd.")
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
             (asset "OMDA" "Omada Health Inc.")
             (asset "DXCM" "Dexcom Inc")
             (asset "GHRS" "GH Research PLC")
             (asset "EXAS" "Exact Sciences Corp.")
             (asset "GH" "Guardant Health Inc")
             (asset "TDOC" "Teladoc Health Inc")
             (asset "PHR" "Phreesia Inc")
             (asset "BFLY" "Butterfly Network Inc")
             (asset "ALIT" "Alight Inc.")
             (asset "WELL" "Welltower Inc.")
             (asset "MRK" "Merck & Co Inc")
             (asset "ABBV" "Abbvie Inc")
             (asset "REGN" "Regeneron Pharmaceuticals, Inc.")
             (asset "VRTX" "Vertex Pharmaceuticals, Inc.")
             (asset "GILD" "Gilead Sciences, Inc.")
             (asset "AMGN" "AMGEN Inc.")
             (asset "GOLD" "Gold.com Inc.")
             (asset "KGC" "Kinross Gold Corp.")
             (asset "AU" "AngloGold Ashanti Plc.")
             (asset "SBSW" "Sibanye Stillwater Ltd")
             (asset "GDXJ" "VanEck Junior Gold Miners ETF")
             (asset "SILJ" "Amplify Junior Silver Miners")
             (asset "PPLT" "abrdn Platinum ETF")
             (asset "PALL" "abrdn Palladium ETF")
             (asset "FCX" "Freeport-McMoRan Inc")
             (asset "ALB" "Albemarle Corp")
             (asset "TMQ" "Trilogy Metals Inc")
             (asset "HBM" "Hudbay Minerals Inc.")
             (asset "VALE" "Vale S.A. - ADR")
             (asset "TECK" "Teck Resources Ltd")
             (asset "USAR" "USA Rare Earth Inc.")
             (asset "UAMY" "United States Antimony Corp")
             (asset "COPX" "Global X Copper Miners ETF")
             (asset "LIT" "Global X Lithium & Battery Tech ETF")
             (asset "SGML" "Sigma Lithium Corporation")
             (asset "NU" "Nu Holdings Ltd")
             (asset "IBKR" "Interactive Brokers Group Inc")
             (asset "MELI" "MercadoLibre Inc")
             (asset "BAM" "Brookfield Asset Management Inc")
             (asset "GRAB" "Grab Holdings Limited")
             (asset "JD" "JD.com Inc - ADR")
             (asset "BIDU" "Baidu Inc - ADR")
             (asset "BILI" "Bilibili Inc - ADR")
             (asset "CARR" "Carrier Global Corp")
             (asset "JCI" "Johnson Controls International plc")
             (asset "PNR" "Pentair plc")
             (asset "XYL" "Xylem Inc")
             (asset "AWK" "American Water Works Co. Inc.")
             (asset "BMI" "Badger Meter Inc.")
             (asset "MOD" "Modine Manufacturing Co.")
             (asset "HON" "Honeywell International Inc")
             (asset "GNRC" "Generac Holdings Inc")
             (asset "BW" "Babcock & Wilcox Enterprises Inc")
             (asset "PRLB" "Proto Labs Inc")
             (asset "MLM" "Martin Marietta Materials, Inc.")
             (asset "VMC" "Vulcan Materials Co")
             (asset "ASPN" "Aspen Aerogels Inc.")
             (asset "NNDM" "Nano Dimension Ltd - ADR")
             (asset "COMM" "CommScope Holding Company Inc")
             (asset "LTRX" "Lantronix Inc")
             (asset "ATEX" "Anterix Inc")
             (asset "OSIS" "OSI Systems, Inc.")
             (asset "RELL" "Richardson Electronics, Ltd.")
             (asset "CMTL" "Comtech Telecommunications Corp.")
             (asset "KULR" "KULR Technology Group Inc")
             (asset "SNT" "Senstar Technologies Corp.")
             (asset "LPTH" "Lightpath Technologies, Inc.")
             (asset "FEIM" "Frequency Electronics, Inc.")
             (asset "KOPN" "Kopin Corp.")
             (asset "WYFI" "Whitefiber Inc.")
             (asset "VICI" "VICI Properties Inc")
             (asset "PSTL" "Postal Realty Trust Inc")
             (asset "CAVA" "Cava Group Inc")
             (asset "SMH" "VanEck Semiconductor ETF")
             (asset "SMHX" "VanEck Fabless Semiconductor ETF")
             (asset "XLK" "Technology Select Sector SPDR ETF")
             (asset "XLI" "Industrial Select Sector SPDR ETF")
             (asset "XME" "SPDR S&P Metals & Mining ETF")
             (asset "SLX" "VanEck Steel ETF")
             (asset "IBIT" "iShares Bitcoin Trust ETF")
             (asset "ETH" "Grayscale Ethereum Mini Trust ETF")
             (asset "WGMI" "CoinShares Bitcoin Mining ETF")
             (asset "GDLC" "Grayscale CoinDesk Crypto 5")
             (asset "BITW" "Bitwise 10 Crypto Index ETF")
             (asset "BLOK" "Amplify Blockchain ETF")
             (asset
              "VIXM"
              "ProShares Trust - ProShares VIX Mid-Term Futures ETF")
             (asset
              "XVOL"
              "Tidal Trust I - Acruence Active Hedge U.S. Equity ETF")
             (asset "NVDL" "GraniteShares 2x Long NVDA Daily ETF")
             (asset "MULL" "GraniteShares 2x Long MU Daily ETF")
             (asset "MVLL" "GraniteShares 2x Long MRVL Daily ETF")
             (asset "AMDU" "Defiance Leveraged Long + Income AMD ETF")
             (asset "TSLL" "Direxion Daily TSLA Bull 2X Shares")
             (asset "TSMU" "GraniteShares 2x Long TSM Daily ETF")
             (asset "SMCX" "Defiance 2x Long SMCI ETF")
             (asset
              "ARMG"
              "Themes ETF Trust - Leverage Shares 2X Long ARM Daily ETF")
             (asset
              "AVGU"
              "GraniteShares ETF Trust - GraniteShares 2x Long AVGO Daily ETF")
             (asset
              "INTW"
              "GraniteShares ETF Trust - GraniteShares 2x Long INTC Daily ETF")
             (asset
              "QCML"
              "GraniteShares ETF Trust - GraniteShares 2x Long QCOM Daily ETF")
             (asset "PTIR" "GraniteShares 2x Long PLTR Daily ETF")
             (asset "NEBX" "Tradr 2X Long NBIS Daily ETF")
             (asset "NETX" "Tradr 2X Long NET Daily ETF")
             (asset "CRWU" "T-REX 2X Long CRWV Daily Target ETF")
             (asset
              "SKYU"
              "ProShares Ultra Nasdaq Cloud Computing ETF")
             (asset "PALU" "Direxion Daily PANW Bull 2X Shares")
             (asset "UCYB" "ProShares Ultra Nasdaq Cybersecurity ETF")
             (asset "TEMT" "Tradr 2X Long TEM Daily ETF")
             (asset
              "APPX"
              "Investment Managers Series Trust II - Tradr 2X Long APP Daily ETF")
             (asset
              "CRWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long CRWD Daily ETF")
             (asset
              "UBOT"
              "Direxion Shares ETF Trust - Daily Robotics, Artificial Intelligence & Automation Index Bull 2X Shares")
             (asset
              "MSFL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MSFT Daily ETF")
             (asset
              "GOOX"
              "ETF Opportunities Trust - T-Rex 2X Long Alphabet Daily Target ETF")
             (asset
              "AMZZ"
              "GraniteShares ETF Trust - GraniteShares 2x Long AMZN Daily ETF")
             (asset
              "FBL"
              "GraniteShares ETF Trust - GraniteShares 2x Long META Daily ETF")
             (asset
              "DLLL"
              "GraniteShares ETF Trust - GraniteShares 2x Long DELL Daily ETF")
             (asset
              "RDTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RDDT Daily ETF")
             (asset
              "VRTL"
              "GraniteShares ETF Trust - GraniteShares 2x Long VRT Daily ETF")
             (asset
              "ORCU"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bull 2X ETF")
             (asset "IONL" "GraniteShares 2x Long IONQ Daily ETF")
             (asset "RGTX" "Defiance 2X Long RGTI Daily ETF")
             (asset "QBTX" "Tradr 2X Long QBTS Daily ETF")
             (asset "QUBX" "Tradr 2X Long QUBT Daily ETF")
             (asset "QPUX" "Defiance 2X Long Pure Quantum ETF")
             (asset "MSTU" "T-Rex 2X Long MSTR Daily Target ETF")
             (asset "CONL" "GraniteShares 2x Long COIN Daily ETF")
             (asset "CIFU" "T-REX 2X Long CIFR Daily Target ETF")
             (asset "BTCL" "T-Rex 2X Long Bitcoin Daily Target ETF")
             (asset "ETHU" "2x Ether ETF")
             (asset "SOLT" "2x Solana ETF")
             (asset "XRPT" "XRP 2X ETF")
             (asset
              "XXRP"
              "Listed Funds Trust - Teucrium 2x Long Daily XRP ETF")
             (asset "HOOG" "Leverage Shares 2X Long HOOD Daily ETF")
             (asset
              "MRAL"
              "GraniteShares ETF Trust - GraniteShares 2x Long MARA Daily ETF")
             (asset
              "BEGS"
              "Collaborative Investment Series Trust - Rareview 2x Bull Cryptocurrency & Precious Metals ETF")
             (asset "RKLX" "Defiance 2X Long RKLB ETF")
             (asset
              "ASTX"
              "Investment Managers Series Trust II - Tradr 2X Long ASTS Daily ETF")
             (asset "AVXX" "Defiance 2x Long AVAV ETF")
             (asset
              "BOEU"
              "Direxion Shares ETF Trust - Direxion Daily BA Bull 2X Shares")
             (asset
              "ARCX"
              "Investment Managers Series Trust II - Tradr 2X Long ACHR Daily ETF")
             (asset
              "PONX"
              "Investment Managers Series Trust II - Tradr 2X Long PONY Daily ETF")
             (asset "ENPX" "Tradr 2X Long ENPH Daily ETF")
             (asset "IREX" "Tradr 2X Long IREN Daily ETF")
             (asset "OKLL" "Defiance 2x Long OKLO ETF")
             (asset "NNEX" "Tradr 2X Long NNE Daily ETF")
             (asset
              "SMU"
              "Investment Managers Series Trust II - Tradr 2X Long SMR Daily ETF")
             (asset "BEX" "Tradr 2X Long BE Daily ETF")
             (asset "GEVX" "Tradr 2X Long GEV Daily ETF")
             (asset "QSX" "Tradr 2X Long QS Daily ETF")
             (asset
              "CEGX"
              "Investment Managers Series Trust II - Tradr 2X Long CEG Daily ETF")
             (asset "ERX" "Direxion Daily Energy Bull 2X Shares")
             (asset "GUSH" "Direxion Daily S&P Oil & Gas Bull 2X")
             (asset "UCO" "ProShares Ultra Bloomberg Crude Oil")
             (asset "BOIL" "ProShares Ultra Bloomberg Natural Gas")
             (asset "UGL" "ProShares Ultra Gold")
             (asset "NUGT" "Direxion Daily Gold Miners Bull 2X")
             (asset "JNUG" "Direxion Daily Junior Gold Miners Bull 2X")
             (asset "AGQ" "ProShares Ultra Silver")
             (asset "CPXR" "USCF Daily Target 2X Copper Index ETF")
             (asset "LLYX" "Defiance 2X Long LLY ETF")
             (asset
              "UNHG"
              "Themes ETF Trust - Leverage Shares 2X Long UNH Daily ETF")
             (asset
              "UPSX"
              "Investment Managers Series Trust II - Tradr 2X Long UPST Daily ETF")
             (asset
              "BABX"
              "GraniteShares ETF Trust - GraniteShares 2x Long BABA Daily ETF")
             (asset
              "PDDL"
              "GraniteShares ETF Trust - GraniteShares 2x Long PDD Daily ETF")
             (asset
              "RVNL"
              "GraniteShares ETF Trust - GraniteShares 2x Long RIVN Daily ETF")
             (asset "NVDQ" "T-Rex 2X Inverse NVIDIA Daily Target ETF")
             (asset "DAMD" "Defiance 2X Short AMD ETF")
             (asset "STSM" "Defiance 2X Short TSM ETF")
             (asset "SMCZ" "Defiance 2X Short SMCI ETF")
             (asset "PLTZ" "Defiance 2x Short PLTR ETF")
             (asset "CORD" "T-REX 2X Inverse CRWV Daily Target ETF")
             (asset
              "ORCS"
              "Direxion Shares ETF Trust - Direxion Daily ORCL Bear 1X ETF")
             (asset "RGTZ" "Defiance 2x Short RGTI ETF")
             (asset "IONZ" "Defiance 2x Short IONQ ETF")
             (asset "QBTZ" "Defiance 2x Short QBTS ETF")
             (asset "MSTZ" "T-Rex 2X Inverse MSTR Daily Target ETF")
             (asset "CONI" "GraniteShares 2x Short COIN Daily ETF")
             (asset "BITI" "ProShares Short Bitcoin ETF")
             (asset
              "SBIT"
              "ProShares Trust - ProShares UltraShort Bitcoin ETF")
             (asset "BTCZ" "T-Rex 2X Inverse Bitcoin Daily Target ETF")
             (asset "ETHD" "ProShares UltraShort Ether ETF")
             (asset "SOLZ" "Solana ETF")
             (asset "XRPZ" "Franklin XRP Trust")
             (asset "HOOZ" "Defiance 2X Short HOOD ETF")
             (asset "REKT" "Direxion Daily Crypto Industry Bear 1X")
             (asset "RKLZ" "Defiance 2x Short RKLB ETF")
             (asset "OKLS" "Defiance 2X Short OKLO ETF")
             (asset "ERY" "Direxion Daily Energy Bear -2X Shares")
             (asset "DRIP" "Direxion Daily S&P Oil & Gas Bear 2X")
             (asset "SCO" "ProShares UltraShort Bloomberg Crude Oil")
             (asset
              "KOLD"
              "ProShares UltraShort Bloomberg Natural Gas")
             (asset
              "GLL"
              "ProShares Trust - ProShares UltraShort Gold -2x Shares")
             (asset "DUST" "Direxion Daily Gold Miners Bear -2X")
             (asset "ZSL" "ProShares UltraShort Silver")
             (asset "LLYZ" "Defiance 2X Short LLY ETF")
             (asset
              "BITX"
              "Volatility Shares Trust - 2x Bitcoin Strategy ETF")
             (asset
              "AAPU"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bull 2X Shares")
             (asset
              "AAPD"
              "Direxion Shares ETF Trust - Direxion Daily AAPL Bear 1X Shares")
             (asset
              "UTSL"
              "Direxion Shares ETF Trust - Direxion Daily Utilities Bull 3X Shares")
             (asset
              "DFEN"
              "Direxion Shares ETF Trust - Direxion Daily Aerospace & Defense Bull 3X Shares")
             (asset
              "LRCU"
              "Investment Managers Series Trust II - Tradr 2X Long LRCX Daily ETF")
             (asset
              "LABX"
              "Investment Managers Series Trust II - Tradr 2X Long ALAB Daily ETF")
             (asset
              "CRDU"
              "Investment Managers Series Trust II - Tradr 2X Long CRDO Daily ETF")
             (asset
              "CRCD"
              "ETF Opportunities Trust - T-REX 2X Inverse CRCL Daily Target ETF")
             (asset
              "DOGD"
              "Investment Managers Series Trust II - Tradr 2X Long DDOG Daily ETF")
             (asset
              "MDBX"
              "Investment Managers Series Trust II - Tradr 2X Long MDB Daily ETF")
             (asset
              "CLSX"
              "Investment Managers Series Trust II - Tradr 2X Long CLSK Daily ETF")
             (asset
              "COZX"
              "Investment Managers Series Trust II - Tradr 2X Long CORZ Daily ETF")
             (asset
              "CSEX"
              "Investment Managers Series Trust II - Tradr 2X Long CLS Daily ETF")
             (asset
              "JOBX"
              "Investment Managers Series Trust II - Tradr 2X Long JOBY Daily ETF")
             (asset
              "OPEX"
              "Investment Managers Series Trust II - Tradr 2X Long OPEN Daily ETF")
             (asset
              "WULX"
              "Investment Managers Series Trust II - Tradr 2X Long WULF Daily ETF")
             (asset
              "ANEL"
              "Tidal Trust II - Defiance Daily Target 2x Long ANET ETF")
             (asset
              "VSTL"
              "Tidal Trust II - Defiance Daily Target 2X Long VST ETF")
             (asset
              "SOUX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOUN ETF")
             (asset
              "RIOX"
              "Tidal Trust II - Defiance Daily Target 2X Long RIOT ETF")
             (asset
              "BU"
              "Tidal Trust II - Defiance Daily Target 2X Long BU ETF")
             (asset
              "SNOU"
              "ETF Opportunities Trust - T-REX 2X Long SNOW Daily Target ETF")
             (asset
              "DKUP"
              "ETF Opportunities Trust - T-REX 2X Long DKNG Daily Target ETF")
             (asset
              "AFRU"
              "ETF Opportunities Trust - T-REX 2X Long AFRM Daily Target ETF")
             (asset
              "KTUP"
              "Investment Managers Series Trust II - T-REX 2X Long KTOS Daily Target ETF")
             (asset
              "GLXU"
              "ETF Opportunities Trust - T-REX 2X Long GLXY Daily Target ETF")
             (asset
              "CCUP"
              "ETF Opportunities Trust - T-REX 2X Long CRCL Daily Target ETF")
             (asset
              "TSLQ"
              "Investment Managers Series Trust II - Tradr 2X Short TSLA Daily ETF")
             (asset
              "NVDS"
              "Investment Managers Series Trust II - Tradr 1.5X Short NVDA Daily ETF")
             (asset
              "SOFX"
              "Tidal Trust II - Defiance Daily Target 2X Long SOFI ETF")
             (asset
              "MPL"
              "Tidal Trust II - Defiance Daily Target 2X Long MP ETF")
             (asset
              "CRMG"
              "Themes ETF Trust - Leverage Shares 2X Long CRM Daily ETF")
             (asset
              "ISUL"
              "GraniteShares ETF Trust - GraniteShares 2x Long ISRG Daily ETF")
             (asset
              "NOWL"
              "GraniteShares ETF Trust - GraniteShares 2x Long NOW Daily ETF")
             (asset
              "PYPG"
              "Themes ETF Trust - Leverage Shares 2X Long PYPL Daily ETF")
             (asset
              "NFXS"
              "Direxion Shares ETF Trust - Direxion Daily NFLX Bear 1X Shares")
             (asset
              "BOED"
              "Direxion Shares ETF Trust - Direxion Daily BA Bear 1X Shares")
             (asset
              "LMTS"
              "Direxion Shares ETF Trust - Direxion Daily LMT Bear 1X ETF")
             (asset
              "XOMZ"
              "Direxion Shares ETF Trust - Direxion Daily XOM Bear 1X Shares")
             (asset
              "PALD"
              "Direxion Shares ETF Trust - Direxion Daily PANW Bear 1X Shares")
             (asset
              "AVS"
              "Direxion Shares ETF Trust - Direxion Daily AVGO Bear 1X Shares")
             (asset
              "QCMD"
              "Direxion Shares ETF Trust - Direxion Daily QCOM Bear 1X ETF")
             (asset
              "MUD"
              "Direxion Shares ETF Trust - Direxion Daily MU Bear 1X Shares")
             (asset
              "MSFD"
              "Direxion Shares ETF Trust - Direxion Daily MSFT Bear 1X Shares")
             (asset
              "METD"
              "Direxion Shares ETF Trust - Direxion Daily META Bear 1X Shares")
             (asset
              "AMZD"
              "Direxion Shares ETF Trust - Direxion Daily AMZN Bear 1X Shares")
             (asset
              "GGLS"
              "Direxion Shares ETF Trust - Direxion Daily GOOGL Bear 1X Shares")
             (asset
              "CSCS"
              "Direxion Shares ETF Trust - Direxion Daily CSCO Bear 1X ETF")
             (asset
              "QQQD"
              "Direxion Shares ETF Trust - Direxion Daily Magnificent 7 Bear 1X Shares")
             (asset
              "SPDN"
              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bear 1X Shares")
             (asset "BIL" "SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "BND"
              "Vanguard Group, Inc. - Vanguard Total Bond Market ETF")
             (asset
              "LACG"
              "Themes ETF Trust - Leverage Shares 2X Long LAC Daily ETF")
             (asset
              "BEG"
              "Themes ETF Trust - Leverage Shares 2x Long BE Daily ETF")
             (asset
              "BIL"
              "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")
             (asset "SLNH" "Soluna Holdings Inc")
             (asset
              "INDI"
              "Indie Semiconductor Inc - Ordinary Shares - Class A")
             (asset "GSIT" "GSI Technology Inc")
             (asset "SLS" "SELLAS Life Sciences Group Inc")
             (asset "SRFM" "Surf Air Mobility Inc")
             (asset
              "PXIU"
              "ETF Opportunities Trust - T-REX 2X Long UPXI Daily Target ETF")
             (asset "DRUG" "Bright Minds Biosciences Inc")
             (asset
              "CWEB"
              "Direxion Shares ETF Trust - Direxion Daily CSI China Internet Index Bull 2X Shares")
             (asset
              "XPP"
              "ProShares Trust - ProShares Ultra FTSE China 50 2x Shares")
             (asset
              "CHAU"
              "Direxion Shares ETF Trust - Direxion Daily CSI 300 China A Share Bull 2X Shares")
             (asset
              "YXI"
              "ProShares Trust - ProShares Short FTSE China 50 -1x Shares")])])])])]
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
