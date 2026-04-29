import psycopg2
import psycopg2.extras
import sqlite3
from nexus.core.config import DATABASE_URL, SQLITE_DB_PATH, DB_BACKEND

# Async URL for ADK
ADK_DATABASE_URL = (
    DATABASE_URL
    .replace("postgresql://", "postgresql+asyncpg://")
    .replace("sslmode=require", "ssl=require")
) if DATABASE_URL.startswith("postgresql") else DATABASE_URL

def get_pg_conn():
    if not DATABASE_URL.startswith("postgresql"):
        return None
    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn

def get_sqlite_conn():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_db_conn():
    """Returns configured DB connection. Defaults to SQLite for local runtime stability."""
    if DB_BACKEND == "postgres" and DATABASE_URL.startswith("postgresql"):
        return get_pg_conn()
    return get_sqlite_conn()
