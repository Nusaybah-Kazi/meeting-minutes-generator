import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

LLM_MODEL = "openai/gpt-oss-120b"        # main model for minutes
FAST_MODEL = "openai/gpt-oss-20b"        # faster model for simple steps
WHISPER_MODEL = "whisper-large-v3-turbo" # audio transcription


def require_api_key() -> str:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY not found. Add it to your .env file (see .env.example)."
        )
    return GROQ_API_KEY