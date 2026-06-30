import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST, before any other imports
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Verify Gemini API key is loaded
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError(f"CRITICAL: GEMINI_API_KEY not found. Looked at: {env_path}")
print(f"✅ Loaded .env from: {env_path}")

# NOW import FastAPI and routers
from fastapi import FastAPI
from backend.routes.screener import router as screener_router

app = FastAPI(
    title="AI Stock Screener API"
)

app.include_router(
    screener_router,
    prefix="/api/screener",
    tags=["screener"]
)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AI Stock Screener API"
    }