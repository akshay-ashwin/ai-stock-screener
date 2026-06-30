import yfinance as yf
from typing import Optional

# NSE tickers (.NS suffix) organized by sector
# These are manually curated since yFinance sector data is unreliable for Indian stocks
STOCK_UNIVERSE = {
    "Banking": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS",
        "AXISBANK.NS", "INDUSINDBK.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS",
        "BANDHANBNK.NS", "PNB.NS", "BANKBARODA.NS", "CANBK.NS"
    ],
    "Finance": [
        "BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS",
        "MANAPPURAM.NS", "LICHSGFIN.NS", "RECLTD.NS", "PFC.NS"
    ],
    "IT": [
        "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS",
        "LTIM.NS", "PERSISTENT.NS", "COFORGE.NS", "MPHASIS.NS",
        "OFSS.NS", "KPITTECH.NS", "TATAELXSI.NS"
    ],
    "Pharma": [
        "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS",
        "AUROPHARMA.NS", "LUPIN.NS", "TORNTPHARM.NS", "ALKEM.NS",
        "ABBOTINDIA.NS", "GLAXO.NS"
    ],
    "Healthcare": [
        "APOLLOHOSP.NS", "FORTIS.NS", "MAXHEALTH.NS", "METROPOLIS.NS",
        "LALPATHLAB.NS", "THYROCARE.NS"
    ],
    "Auto": [
        "MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS",
        "HEROMOTOCO.NS", "EICHERMOT.NS", "ASHOKLEY.NS", "TVSMOTOR.NS",
        "BALKRISIND.NS", "MOTHERSON.NS"
    ],
    "FMCG": [
        "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS",
        "DABUR.NS", "GODREJCP.NS", "MARICO.NS", "COLPAL.NS",
        "EMAMILTD.NS", "TATACONSUM.NS", "UNITDSPR.NS"
    ],
    "Energy": [
        "RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS", "GAIL.NS",
        "POWERGRID.NS", "NTPC.NS", "ADANIGREEN.NS", "TATAPOWER.NS",
        "TORNTPOWER.NS", "CESC.NS"
    ],
    "Metal": [
        "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "COALINDIA.NS",
        "VEDL.NS", "NMDC.NS", "SAIL.NS", "NATIONALUM.NS", "JINDALSTEL.NS"
    ],
    "Infra": [
        "LT.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS", "SHREECEM.NS",
        "ACC.NS", "AMBUJACEMENT.NS", "DELHIVERY.NS", "IRCTC.NS",
        "GMRINFRA.NS", "IRB.NS"
    ],
    "Telecom": [
        "BHARTIARTL.NS", "INDUSTOWER.NS"
    ],
}

ALL_TICKERS = [t for tickers in STOCK_UNIVERSE.values() for t in tickers]

# Reverse map: ticker → sector (for fast lookup)
TICKER_SECTOR = {
    ticker: sector
    for sector, tickers in STOCK_UNIVERSE.items()
    for ticker in tickers
}


def get_tickers_for_sectors(sectors: Optional[list]) -> list:
    # Handle ["All"] or empty sectors - return all tickers
    if not sectors or "All" in sectors:
        return ALL_TICKERS
    result = []
    for sector in sectors:
        result.extend(STOCK_UNIVERSE.get(sector, []))
    return result


def fetch_stock_info(ticker: str) -> Optional[dict]:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if not price:
            return None

        market_cap = info.get("marketCap") or 0
        market_cap_cr = round(market_cap / 1e7, 2)  # Convert to crores

        roe = info.get("returnOnEquity")
        debt_to_equity = info.get("debtToEquity")
        # yFinance gives D/E as a percentage for some stocks (e.g. 45.2 means 0.452)
        # Normalize it
        if debt_to_equity and debt_to_equity > 20:
            debt_to_equity = debt_to_equity / 100

        clean_ticker = ticker.replace(".NS", "").replace(".BO", "")

        return {
            "ticker": clean_ticker,
            "nse_symbol": ticker,
            "name": info.get("longName") or info.get("shortName", clean_ticker),
            "sector": TICKER_SECTOR.get(ticker, "Unknown"),
            "price": round(price, 2),
            "market_cap_cr": market_cap_cr,
            "pe_ratio": round(info.get("trailingPE"), 2) if info.get("trailingPE") else None,
            "forward_pe": round(info.get("forwardPE"), 2) if info.get("forwardPE") else None,
            "roe": round(roe, 4) if roe else None,
            "debt_to_equity": round(debt_to_equity, 2) if debt_to_equity else None,
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "profit_margin": info.get("profitMargins"),
            "dividend_yield": info.get("dividendYield"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "book_value": info.get("bookValue"),
            "price_to_book": info.get("priceToBook"),
            "recommendation": info.get("recommendationKey"),
        }
    except Exception:
        return None


def fetch_stocks(tickers: list) -> list:
    results = []
    for ticker in tickers:
        data = fetch_stock_info(ticker)
        if data:
            results.append(data)
    return results


def apply_filters(stocks: list, filters: dict) -> list:
    f = filters  # shorthand

    def passes(s):
        if f.get("sectors") and "All" not in f["sectors"] and s["sector"] not in f["sectors"]:
            return False
        if f.get("max_pe") is not None:
            if not s["pe_ratio"] or s["pe_ratio"] <= 0 or s["pe_ratio"] > f["max_pe"]:
                return False
        if f.get("min_pe") is not None:
            if not s["pe_ratio"] or s["pe_ratio"] < f["min_pe"]:
                return False
        if f.get("min_roe") is not None:
            if not s["roe"] or s["roe"] < f["min_roe"]:
                return False
        if f.get("max_roe") is not None:
            if not s["roe"] or s["roe"] > f["max_roe"]:
                return False
        if f.get("max_debt_to_equity") is not None:
            if s["debt_to_equity"] is None or s["debt_to_equity"] > f["max_debt_to_equity"]:
                return False
        if f.get("min_revenue_growth") is not None:
            if not s["revenue_growth"] or s["revenue_growth"] < f["min_revenue_growth"]:
                return False
        if f.get("min_earnings_growth") is not None:
            if not s["earnings_growth"] or s["earnings_growth"] < f["min_earnings_growth"]:
                return False
        if f.get("min_profit_margin") is not None:
            if not s["profit_margin"] or s["profit_margin"] < f["min_profit_margin"]:
                return False
        if f.get("min_market_cap_cr") is not None:
            if s["market_cap_cr"] < f["min_market_cap_cr"]:
                return False
        if f.get("max_market_cap_cr") is not None:
            if s["market_cap_cr"] > f["max_market_cap_cr"]:
                return False
        if f.get("min_dividend_yield") is not None:
            if not s["dividend_yield"] or s["dividend_yield"] < f["min_dividend_yield"]:
                return False
        return True

    # Filter stocks
    filtered = [s for s in stocks if passes(s)]

    # Apply sorting
    sort_by = f.get("sort_by")
    sort_order = f.get("sort_order", "desc")
    
    if sort_by:
        reverse = (sort_order == "desc")
        # Sort by the specified metric, putting None values at the end
        filtered.sort(
            key=lambda s: (s.get(sort_by) is None, s.get(sort_by) or 0),
            reverse=reverse
        )

    # Apply limit
    limit = f.get("limit", 10)
    return filtered[:limit]