import yfinance as yf
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# NSE tickers (.NS suffix) organized by sector
# Manually curated — yFinance sector data is unreliable for Indian stocks
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

# Fields that can be sorted — maps API sort_by name → dict key
SORTABLE_FIELDS = {
    "roe": "roe",
    "pe_ratio": "pe_ratio",
    "market_cap_cr": "market_cap_cr",
    "revenue_growth": "revenue_growth",
    "earnings_growth": "earnings_growth",
    "debt_to_equity": "debt_to_equity",
    "dividend_yield": "dividend_yield",
    "price": "price",
    "profit_margin": "profit_margin",
}


def get_tickers_for_sectors(sectors: Optional[list]) -> list:
    """Return tickers for given sectors. None or ['All'] → all tickers."""
    if not sectors or sectors == ["All"]:
        return ALL_TICKERS
    result = []
    for sector in sectors:
        result.extend(STOCK_UNIVERSE.get(sector, []))
    return result


def fetch_stock_info(ticker: str) -> Optional[dict]:
    """Fetch and normalize a single stock from yFinance. Returns None on failure."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if not price:
            return None  # Skip stocks with no price data

        market_cap = info.get("marketCap") or 0
        market_cap_cr = round(market_cap / 1e7, 2)  # Convert to Indian crores

        roe = info.get("returnOnEquity")
        debt_to_equity = info.get("debtToEquity")

        # yFinance gives D/E as percentage for some Indian stocks (45.2 means 0.452)
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
            "week_52_high": info.get("fiftyTwoWeekHigh"),
            "week_52_low": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "book_value": info.get("bookValue"),
            "price_to_book": info.get("priceToBook"),
            "recommendation": info.get("recommendationKey"),
        }
    except Exception:
        return None  # Silently skip — 404s and rate limits are common


def fetch_stocks(tickers: list, max_workers: int = 10) -> list:
    """
    Fetch multiple stocks in parallel using a thread pool.

    Why threads and not asyncio? yFinance is a synchronous library with no async
    support. ThreadPoolExecutor lets us run multiple blocking HTTP calls at once
    without rewriting yFinance internals. 10 workers is the sweet spot — more
    workers hit yFinance rate limits, fewer and we lose parallelism benefit.

    Speed improvement: 100 stocks sequentially ≈ 40s. With 10 workers ≈ 4-6s.
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(fetch_stock_info, ticker): ticker
            for ticker in tickers
        }
        for future in as_completed(future_to_ticker):
            data = future.result()
            if data:
                results.append(data)
    return results


def apply_filters(stocks: list, filters: dict) -> list:
    """Filter stocks based on parsed filter criteria. All filters are optional."""
    f = filters

    def passes(s):
        # Sector filter — handled at ticker selection level too, but double-check
        if f.get("sectors") and f["sectors"] != ["All"]:
            if s["sector"] not in f["sectors"]:
                return False

        # P/E filters — exclude stocks with missing or negative P/E
        if f.get("max_pe") is not None:
            if not s["pe_ratio"] or s["pe_ratio"] <= 0 or s["pe_ratio"] > f["max_pe"]:
                return False
        if f.get("min_pe") is not None:
            if not s["pe_ratio"] or s["pe_ratio"] < f["min_pe"]:
                return False

        # ROE filter (stored as decimal: 0.15 = 15%)
        if f.get("min_roe") is not None:
            if not s["roe"] or s["roe"] < f["min_roe"]:
                return False

        # Debt/equity filter
        if f.get("max_debt_to_equity") is not None:
            if s["debt_to_equity"] is None or s["debt_to_equity"] > f["max_debt_to_equity"]:
                return False

        # Growth filters
        if f.get("min_revenue_growth") is not None:
            if not s["revenue_growth"] or s["revenue_growth"] < f["min_revenue_growth"]:
                return False
        if f.get("min_earnings_growth") is not None:
            if not s["earnings_growth"] or s["earnings_growth"] < f["min_earnings_growth"]:
                return False

        # Profitability filters
        if f.get("min_profit_margin") is not None:
            if not s["profit_margin"] or s["profit_margin"] < f["min_profit_margin"]:
                return False

        # Market cap filters
        if f.get("min_market_cap_cr") is not None:
            if s["market_cap_cr"] < f["min_market_cap_cr"]:
                return False
        if f.get("max_market_cap_cr") is not None:
            if s["market_cap_cr"] > f["max_market_cap_cr"]:
                return False

        # Dividend filter
        if f.get("min_dividend_yield") is not None:
            if not s["dividend_yield"] or s["dividend_yield"] < f["min_dividend_yield"]:
                return False

        return True

    return [s for s in stocks if passes(s)]


def sort_results(stocks: list, sort_by: Optional[str], sort_order: str = "desc") -> list:
    """
    Sort stocks by any numeric field.

    Stocks missing the sort field are pushed to the end regardless of sort order —
    you don't want nulls floating to the top of "best ROE" results.
    """
    field = SORTABLE_FIELDS.get(sort_by) if sort_by else None

    if not field:
        # Default: sort by market cap descending (largest companies first)
        return sorted(stocks, key=lambda s: s.get("market_cap_cr") or 0, reverse=True)

    reverse = sort_order.lower() != "asc"

    return sorted(
        stocks,
        key=lambda s: (
            s.get(field) is None,    # None values sink to the bottom
            s.get(field) or 0
        ),
        reverse=reverse
    )


def run_screener(filters: dict) -> list:
    """
    Full pipeline: sector selection → parallel fetch → filter → sort → limit.
    This is the single entry point the route layer calls.
    """
    sectors = filters.get("sectors")
    tickers = get_tickers_for_sectors(sectors)

    stocks = fetch_stocks(tickers)
    stocks = apply_filters(stocks, filters)
    stocks = sort_results(stocks, filters.get("sort_by"), filters.get("sort_order", "desc"))

    limit = filters.get("limit", 10)
    return stocks[:limit]
