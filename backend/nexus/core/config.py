import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# Database
_default_sqlite = str((BACKEND_DIR / "nexus.db").resolve()).replace("\\", "/")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{_default_sqlite}")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", str((BACKEND_DIR / "nexus.db").resolve()))
DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").lower().strip()

# Platform Settings
PLATFORM_NAME = "NEXUS Supply Chain Intelligence Platform"
VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ENABLE_A2A = os.getenv("ENABLE_A2A", "false").lower() == "true"
PORT = int(os.getenv("PORT", 8010))
HOST = os.getenv("HOST", "0.0.0.0")
