import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

# Original sync URL for psycopg2
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found. Make sure .env exists and contains DATABASE_URL.")

# Async URL for ADK — derived from original, never stored in .env
ADK_DATABASE_URL = (
    DATABASE_URL
    .replace("postgresql://", "postgresql+asyncpg://")
    .replace("sslmode=require", "ssl=require")
)

def get_conn():
    conn = psycopg2.connect(
        DATABASE_URL,  # ← always uses original sync URL
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn