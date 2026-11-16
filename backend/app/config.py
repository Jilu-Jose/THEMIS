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
if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    DATA_DIR = Path(os.getenv("THEMIS_DATA_DIR", "/tmp/themis_data"))
else:
    DATA_DIR = Path(os.getenv("THEMIS_DATA_DIR", BACKEND_DIR / "data"))
SESSIONS_DIR = DATA_DIR / "sessions"
try:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    DATA_DIR = Path("/tmp/themis_data")
    SESSIONS_DIR = DATA_DIR / "sessions"
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
DEFAULT_MODEL = os.getenv("THEMIS_MODEL", "openai/gpt-oss-120b")
MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]

# Default settings for evaluation sessions
DEFAULT_SETTINGS = {
    "model": DEFAULT_MODEL,
    "reasoning_effort": "medium",      # low | medium | high
    "low_price_ratio": 0.60,           # price < 60% of median  => abnormally low
    "high_price_ratio": 1.40,          # price > 140% of median => abnormally high
    "similarity_threshold": 0.35,      # shingle-Jaccard above this => copied-text flag
    "blind_technical": True,           # anonymise bidders during technical scoring
}


def llm_mode() -> str:
    """'groq' when GROQ_API_KEY is configured, else 'unconfigured'."""
    return "groq" if GROQ_API_KEY else "unconfigured"
