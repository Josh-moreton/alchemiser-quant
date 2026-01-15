"""Business Unit: shared | Status: current.

Ticker-to-sector ETF mapping for options hedging.

Maps individual equity tickers to liquid sector ETFs (QQQ, SPY, XLK, etc.)
to enable efficient hedging via options on highly liquid underlying instruments.

Benefits of sector-based hedging:
- Tighter bid-ask spreads (penny-wide for QQQ/SPY vs $0.10+ for individuals)
- Lower transaction costs (fewer contracts to manage)
- Simpler position management during rolls
- High correlation to individual holdings (~0.85+ for tech stocks to QQQ)
"""

from __future__ import annotations

# Ticker to hedge ETF mapping
# Technology stocks map to QQQ (Nasdaq 100)
# Financials map to XLF
# Other sectors map to their respective SPDR sector ETFs
# Unmapped tickers default to SPY (broad market hedge)

TICKER_SECTOR_MAP: dict[str, str] = {
    # ═══════════════════════════════════════════════════════════════════════════
    # TECHNOLOGY → QQQ (Nasdaq 100) - Primary hedge for tech-heavy portfolios
    # ═══════════════════════════════════════════════════════════════════════════
    "AAPL": "QQQ",
    "MSFT": "QQQ",
    "NVDA": "QQQ",
    "GOOGL": "QQQ",
    "GOOG": "QQQ",
    "META": "QQQ",
    "AVGO": "QQQ",
    "ORCL": "QQQ",
    "CRM": "QQQ",
    "ADBE": "QQQ",
    "AMD": "QQQ",
    "INTC": "QQQ",
    "CSCO": "QQQ",
    "QCOM": "QQQ",
    "TXN": "QQQ",
    "IBM": "QQQ",
    "AMAT": "QQQ",
    "MU": "QQQ",
    "LRCX": "QQQ",
    "KLAC": "QQQ",
    "SNPS": "QQQ",
    "CDNS": "QQQ",
    "MRVL": "QQQ",
    "NXPI": "QQQ",
    "ADI": "QQQ",
    "PANW": "QQQ",
    "FTNT": "QQQ",
    "CRWD": "QQQ",
    "NOW": "QQQ",
    "INTU": "QQQ",
    "WDAY": "QQQ",
    "SNOW": "QQQ",
    "PLTR": "QQQ",
    "DDOG": "QQQ",
    "NET": "QQQ",
    "ZS": "QQQ",
    "TEAM": "QQQ",
    "SHOP": "QQQ",
    "SQ": "QQQ",
    "COIN": "QQQ",
    "UBER": "QQQ",
    "ABNB": "QQQ",
    "DASH": "QQQ",
    "RBLX": "QQQ",
    "ROKU": "QQQ",
    "SNAP": "QQQ",
    "PINS": "QQQ",
    "TTD": "QQQ",
    "U": "QQQ",
    "TWLO": "QQQ",
    "OKTA": "QQQ",
    "MDB": "QQQ",
    "DOCU": "QQQ",
    "ZM": "QQQ",
    "VEEV": "QQQ",
    "SPLK": "QQQ",
    "ESTC": "QQQ",
    "PATH": "QQQ",
    "CFLT": "QQQ",
    # ═══════════════════════════════════════════════════════════════════════════
    # LEVERAGED ETFs → Map to their underlying index
    # ═══════════════════════════════════════════════════════════════════════════
    "TQQQ": "QQQ",  # 3x Nasdaq
    "SQQQ": "QQQ",  # -3x Nasdaq
    "QLD": "QQQ",  # 2x Nasdaq
    "QID": "QQQ",  # -2x Nasdaq
    "SPXL": "SPY",  # 3x S&P 500
    "SPXS": "SPY",  # -3x S&P 500
    "SSO": "SPY",  # 2x S&P 500
    "SH": "SPY",  # -1x S&P 500
    "SDS": "SPY",  # -2x S&P 500
    "UPRO": "SPY",  # 3x S&P 500
    "SPUU": "SPY",  # 2x S&P 500
    "TNA": "IWM",  # 3x Russell 2000
    "TZA": "IWM",  # -3x Russell 2000
    "UWM": "IWM",  # 2x Russell 2000
    "TWM": "IWM",  # -2x Russell 2000
    # ═══════════════════════════════════════════════════════════════════════════
    # FINANCIALS → XLF (Financial Select Sector SPDR)
    # ═══════════════════════════════════════════════════════════════════════════
    "JPM": "XLF",
    "BAC": "XLF",
    "WFC": "XLF",
    "GS": "XLF",
    "MS": "XLF",
    "C": "XLF",
    "BLK": "XLF",
    "SCHW": "XLF",
    "AXP": "XLF",
    "V": "XLF",
    "MA": "XLF",
    "PYPL": "XLF",
    "COF": "XLF",
    "USB": "XLF",
    "PNC": "XLF",
    "TFC": "XLF",
    "BK": "XLF",
    "STT": "XLF",
    "AIG": "XLF",
    "MET": "XLF",
    "PRU": "XLF",
    "AFL": "XLF",
    "CB": "XLF",
    "MMC": "XLF",
    "AON": "XLF",
    "ICE": "XLF",
    "CME": "XLF",
    "SPGI": "XLF",
    "MCO": "XLF",
    "MSCI": "XLF",
    # ═══════════════════════════════════════════════════════════════════════════
    # HEALTHCARE → XLV (Health Care Select Sector SPDR)
    # ═══════════════════════════════════════════════════════════════════════════
    "JNJ": "XLV",
    "UNH": "XLV",
    "PFE": "XLV",
    "ABBV": "XLV",
    "MRK": "XLV",
    "LLY": "XLV",
    "TMO": "XLV",
    "ABT": "XLV",
    "DHR": "XLV",
    "BMY": "XLV",
    "AMGN": "XLV",
    "GILD": "XLV",
    "ISRG": "XLV",
    "SYK": "XLV",
    "VRTX": "XLV",
    "REGN": "XLV",
    "BSX": "XLV",
    "ZBH": "XLV",
    "MDT": "XLV",
    "EW": "XLV",
    "CI": "XLV",
    "ELV": "XLV",
    "HUM": "XLV",
    "CVS": "XLV",
    "MCK": "XLV",
    "CAH": "XLV",
    "ABC": "XLV",
    # ═══════════════════════════════════════════════════════════════════════════
    # CONSUMER DISCRETIONARY → XLY (Consumer Discretionary Select Sector SPDR)
    # ═══════════════════════════════════════════════════════════════════════════
    "AMZN": "XLY",
    "TSLA": "XLY",
    "HD": "XLY",
    "MCD": "XLY",
    "NKE": "XLY",
    "SBUX": "XLY",
    "LOW": "XLY",
    "TJX": "XLY",
    "BKNG": "XLY",
    "CMG": "XLY",
    "MAR": "XLY",
    "HLT": "XLY",
    "ROST": "XLY",
    "ORLY": "XLY",
    "AZO": "XLY",
    "YUM": "XLY",
    "DPZ": "XLY",
    "POOL": "XLY",
    "DHI": "XLY",
    "LEN": "XLY",
    "PHM": "XLY",
    "NVR": "XLY",
    "GM": "XLY",
    "F": "XLY",
    "RIVN": "XLY",
    "LCID": "XLY",
    # ═══════════════════════════════════════════════════════════════════════════
    # ENERGY → XLE (Energy Select Sector SPDR)
    # ═══════════════════════════════════════════════════════════════════════════
    "XOM": "XLE",
    "CVX": "XLE",
    "COP": "XLE",
    "SLB": "XLE",
    "EOG": "XLE",
    "MPC": "XLE",
    "PSX": "XLE",
    "VLO": "XLE",
    "OXY": "XLE",
    "HAL": "XLE",
    "BKR": "XLE",
    "PXD": "XLE",
    "DVN": "XLE",
    "HES": "XLE",
    "FANG": "XLE",
    "WMB": "XLE",
    "KMI": "XLE",
    "OKE": "XLE",
    "TRGP": "XLE",
    "LNG": "XLE",
    # ═══════════════════════════════════════════════════════════════════════════
    # INDUSTRIALS → XLI (Industrial Select Sector SPDR)
    # ═══════════════════════════════════════════════════════════════════════════
    "CAT": "XLI",
    "BA": "XLI",
    "UNP": "XLI",
    "HON": "XLI",
    "RTX": "XLI",
    "GE": "XLI",
    "DE": "XLI",
    "LMT": "XLI",
    "UPS": "XLI",
    "MMM": "XLI",
    "FDX": "XLI",
    "CSX": "XLI",
    "NSC": "XLI",
    "GD": "XLI",
    "NOC": "XLI",
    "ITW": "XLI",
    "EMR": "XLI",
    "ETN": "XLI",
    "PH": "XLI",
    "ROK": "XLI",
    "AME": "XLI",
    "CTAS": "XLI",
    "PCAR": "XLI",
    "CARR": "XLI",
    "OTIS": "XLI",
    "TT": "XLI",
    "WM": "XLI",
    "RSG": "XLI",
    "GWW": "XLI",
    "FAST": "XLI",
    # ═══════════════════════════════════════════════════════════════════════════
    # CONSUMER STAPLES → XLP (Consumer Staples Select Sector SPDR)
    # ═══════════════════════════════════════════════════════════════════════════
    "PG": "XLP",
    "KO": "XLP",
    "PEP": "XLP",
    "COST": "XLP",
    "WMT": "XLP",
    "PM": "XLP",
    "MO": "XLP",
    "CL": "XLP",
    "MDLZ": "XLP",
    "KHC": "XLP",
    "EL": "XLP",
    "GIS": "XLP",
    "K": "XLP",
    "SYY": "XLP",
    "HSY": "XLP",
    "KMB": "XLP",
    "CHD": "XLP",
    "KR": "XLP",
    "TGT": "XLP",
    "DG": "XLP",
    "DLTR": "XLP",
    "ADM": "XLP",
    "BG": "XLP",
    "TSN": "XLP",
    "HRL": "XLP",
    "CAG": "XLP",
    "CPB": "XLP",
    "SJM": "XLP",
    "MKC": "XLP",
    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITIES → XLU (Utilities Select Sector SPDR)
    # ═══════════════════════════════════════════════════════════════════════════
    "NEE": "XLU",
    "DUK": "XLU",
    "SO": "XLU",
    "D": "XLU",
    "AEP": "XLU",
    "SRE": "XLU",
    "XEL": "XLU",
    "EXC": "XLU",
    "ED": "XLU",
    "WEC": "XLU",
    "ES": "XLU",
    "PEG": "XLU",
    "AWK": "XLU",
    "DTE": "XLU",
    "PPL": "XLU",
    "AES": "XLU",
    "FE": "XLU",
    "CMS": "XLU",
    "EVRG": "XLU",
    "ATO": "XLU",
    "NI": "XLU",
    "NRG": "XLU",
    "ETR": "XLU",
    "CNP": "XLU",
    "LNT": "XLU",
    # ═══════════════════════════════════════════════════════════════════════════
    # REAL ESTATE → XLRE (Real Estate Select Sector SPDR)
    # ═══════════════════════════════════════════════════════════════════════════
    "AMT": "XLRE",
    "PLD": "XLRE",
    "EQIX": "XLRE",
    "CCI": "XLRE",
    "SPG": "XLRE",
    "PSA": "XLRE",
    "O": "XLRE",
    "DLR": "XLRE",
    "WELL": "XLRE",
    "AVB": "XLRE",
    "EQR": "XLRE",
    "SBAC": "XLRE",
    "ARE": "XLRE",
    "VTR": "XLRE",
    "MAA": "XLRE",
    "UDR": "XLRE",
    "ESS": "XLRE",
    "CPT": "XLRE",
    "EXR": "XLRE",
    "CUBE": "XLRE",
    "REG": "XLRE",
    "KIM": "XLRE",
    "BXP": "XLRE",
    "SLG": "XLRE",
    "VNO": "XLRE",
    "HST": "XLRE",
    "PEAK": "XLRE",
    "INVH": "XLRE",
    # ═══════════════════════════════════════════════════════════════════════════
    # MATERIALS → XLB (Materials Select Sector SPDR)
    # ═══════════════════════════════════════════════════════════════════════════
    "LIN": "XLB",
    "APD": "XLB",
    "SHW": "XLB",
    "FCX": "XLB",
    "NEM": "XLB",
    "ECL": "XLB",
    "DD": "XLB",
    "DOW": "XLB",
    "NUE": "XLB",
    "VMC": "XLB",
    "MLM": "XLB",
    "PPG": "XLB",
    "ALB": "XLB",
    "CTVA": "XLB",
    "IFF": "XLB",
    "FMC": "XLB",
    "CE": "XLB",
    "EMN": "XLB",
    "PKG": "XLB",
    "IP": "XLB",
    "BALL": "XLB",
    "AVY": "XLB",
    "CF": "XLB",
    "MOS": "XLB",
    # ═══════════════════════════════════════════════════════════════════════════
    # COMMUNICATION SERVICES → XLC (Communication Services Select Sector SPDR)
    # ═══════════════════════════════════════════════════════════════════════════
    "NFLX": "XLC",
    "DIS": "XLC",
    "CMCSA": "XLC",
    "T": "XLC",
    "VZ": "XLC",
    "TMUS": "XLC",
    "CHTR": "XLC",
    "EA": "XLC",
    "ATVI": "XLC",
    "TTWO": "XLC",
    "WBD": "XLC",
    "PARA": "XLC",
    "FOX": "XLC",
    "FOXA": "XLC",
    "NWSA": "XLC",
    "NWS": "XLC",
    "LYV": "XLC",
    "OMC": "XLC",
    "IPG": "XLC",
}


def get_hedge_etf(ticker: str) -> str:
    """Get the appropriate hedge ETF for a given ticker.

    Maps individual equity tickers to liquid sector ETFs for hedging.
    Returns SPY as the default for unmapped tickers (broad market hedge).

    Args:
        ticker: The equity ticker symbol (case-insensitive)

    Returns:
        The hedge ETF symbol (QQQ, SPY, XLF, etc.)

    Examples:
        >>> get_hedge_etf("AAPL")
        'QQQ'
        >>> get_hedge_etf("JPM")
        'XLF'
        >>> get_hedge_etf("UNKNOWN")
        'SPY'

    """
    return TICKER_SECTOR_MAP.get(ticker.upper(), "SPY")
