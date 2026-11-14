"""Runtime configuration for T.H.E.M.I.S (read from environment / .env)."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:  # python-dotenv is optional
    pass

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = Path(os.getenv("THEMIS_DATA_DIR", BACKEND_DIR / "data"))
SESSIONS_DIR = DATA_DIR / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
DEFAULT_MODEL = os.getenv("THEMIS_MODEL", "openai/gpt-oss-120b")
MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]

# THEMIS_DEMO=1 forces the offline rule-based engine even when a key is present.
FORCE_DEMO = os.getenv("THEMIS_DEMO", "0") == "1"
# Cosmetic pause per stage in demo mode so the live progress animation is visible.
DEMO_STAGE_DELAY = float(os.getenv("THEMIS_DEMO_DELAY", "0.9"))

DEFAULT_SETTINGS = {
    "model": DEFAULT_MODEL,
    "reasoning_effort": "medium",      # low | medium | high
    "low_price_ratio": 0.60,           # price < 60% of median  => abnormally low
    "high_price_ratio": 1.40,          # price > 140% of median => abnormally high
    "similarity_threshold": 0.35,      # shingle-Jaccard above this => copied-text flag
    "blind_technical": True,           # anonymise bidders during technical scoring
}


def llm_mode() -> str:
    """'groq' when a key is configured and demo is not forced, else 'demo'."""
    return "groq" if (GROQ_API_KEY and not FORCE_DEMO) else "demo"
