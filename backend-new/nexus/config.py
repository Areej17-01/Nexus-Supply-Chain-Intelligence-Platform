import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
PROJECT_ROOT = BASE_DIR.parents[1]
load_dotenv(PROJECT_ROOT / ".env")

PLATFORM_NAME = os.getenv("PLATFORM_NAME", "NEXUS Procurement System")
VERSION = os.getenv("VERSION", "2.0.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8010"))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'nexus.db'}")
ADK_DATABASE_URL = os.getenv(
    "ADK_DATABASE_URL",
    f"sqlite+aiosqlite:///{ROOT_DIR / 'adk_sessions.db'}",
)

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")

A2A_SUPPLIER_URL = os.getenv(
    "A2A_SUPPLIER_URL",
    f"http://127.0.0.1:{PORT}/supplier/a2a/QuoteAgent",
)
A2A_BUYER_URL = os.getenv(
    "A2A_BUYER_URL",
    f"http://127.0.0.1:{PORT}/buyer/a2a/BuyerAgent",
)
