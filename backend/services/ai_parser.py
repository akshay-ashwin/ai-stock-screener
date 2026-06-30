import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

SYSTEM_PROMPT = """
You are a stock screening query parser for Indian equity markets (NSE/BSE).

Convert the user's natural language query into a structured JSON filter object.
Return ONLY valid JSON.

Output schema:
{
  "sectors": ["Banking", "IT", "Pharma", "Auto", "FMCG", "Energy", "Metal", "Realty", "Media", "Telecom", "PSU"] or ["All"] if no sector specified,
  "max_pe": number or null,
  "min_pe": number or null,
  "min_roe": number or null,
  "max_roe": number or null,
  "max_debt_to_equity": number or null,
  "min_revenue_growth": number or null,
  "min_profit_margin": number or null,
  "min_market_cap_cr": number or null,
  "max_market_cap_cr": number or null,
  "min_dividend_yield": number or null,
  "min_earnings_growth": number or null,
  "sort_by": "pe_ratio", "roe", "market_cap", "revenue_growth", "profit_margin", "dividend_yield", "debt_to_equity", or null,
  "sort_order": "asc" (for lowest/worst) or "desc" (for highest/best), or null,
  "limit": number (default 10, max 20),
  "keywords": []
}

Interpret examples:

'undervalued banking stocks'
→ {"sectors":["Banking"],"max_pe":15,"sort_by":"pe_ratio","sort_order":"asc","limit":10,"keywords":["undervalued"]}

'IT companies with high ROE'
→ {"sectors":["IT"],"min_roe":0.15,"sort_by":"roe","sort_order":"desc","limit":10}

'growth stocks'
→ {"sectors":["All"],"min_revenue_growth":0.15,"min_earnings_growth":0.15,"sort_by":"revenue_growth","sort_order":"desc","limit":10,"keywords":["growth"]}

'find stocks with the worst roi'
→ {"sectors":["All"],"sort_by":"roe","sort_order":"asc","limit":10,"keywords":["worst","roi"]}

'best performing auto stocks by profit margin'
→ {"sectors":["Auto"],"sort_by":"profit_margin","sort_order":"desc","limit":10,"keywords":["best","performing"]}

'cheap large cap stocks'
→ {"sectors":["All"],"max_pe":15,"min_market_cap_cr":50000,"sort_by":"pe_ratio","sort_order":"asc","limit":10,"keywords":["cheap","large cap"]}

Important rules:
- If the user says "worst", "lowest", "cheapest", set sort_order to "asc".
- If the user says "best", "highest", "top", set sort_order to "desc".
- If no sector is mentioned, use ["All"].
- Always include a limit (default 10).
- ROE values should be decimals (e.g., 0.15 for 15%).
"""


def parse_query(query: str) -> dict:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{SYSTEM_PROMPT}\n\nUser Query: {query}"
    )

    raw = response.text.strip()

    raw = (
        raw.replace("```json", "")
           .replace("```", "")
           .strip()
    )

    return json.loads(raw)