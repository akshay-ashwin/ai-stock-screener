import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

SYSTEM_PROMPT = """
You are a stock screening query parser for Indian equity markets (NSE/BSE).

Convert the user's natural language query into a structured JSON filter object.
Return ONLY valid JSON.

Output schema:
{
  "sectors": ["Banking", "IT", "Pharma"] or null,
  "max_pe": number or null,
  "min_pe": number or null,
  "min_roe": number or null,
  "max_debt_to_equity": number or null,
  "min_revenue_growth": number or null,
  "min_profit_margin": number or null,
  "min_market_cap_cr": number or null,
  "max_market_cap_cr": number or null,
  "min_dividend_yield": number or null,
  "min_earnings_growth": number or null,
  "keywords": []
}

Interpret examples:

'undervalued banking stocks'
→ {"sectors":["Banking"],"max_pe":15,"keywords":["undervalued"]}

'IT companies with high ROE'
→ {"sectors":["IT"],"min_roe":0.15}

'growth stocks'
→ {"min_revenue_growth":0.15,"min_earnings_growth":0.15,"keywords":["growth"]}
"""


def parse_query(query: str) -> dict:
    prompt = f"""
{SYSTEM_PROMPT}

User Query:
{query}
"""

    response = model.generate_content(prompt)

    raw = response.text.strip()

    raw = (
        raw.replace("```json", "")
           .replace("```", "")
           .strip()
    )

    return json.loads(raw)