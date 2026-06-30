from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.ai_parser import parse_query
from backend.services.stock_fetcher import (
    get_tickers_for_sectors,
    fetch_stocks,
    apply_filters,
)

router = APIRouter()


class ScreenerRequest(BaseModel):
    query: str


@router.post("/search")
def screen_stocks(request: ScreenerRequest):

    filters = parse_query(request.query)

    tickers = get_tickers_for_sectors(
        filters.get("sectors")
    )

    stocks = fetch_stocks(tickers)

    results = apply_filters(
        stocks,
        filters
    )

    return {
        "query": request.query,
        "parsed_filters": filters,
        "count": len(results),
        "results": results
    }