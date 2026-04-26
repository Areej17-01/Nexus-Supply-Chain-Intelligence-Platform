import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv



load_dotenv()
 
DATABASE_URL = os.getenv("DATABASE_URL")
 
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found. Make sure .env exists and contains DATABASE_URL.")
 
 
def get_conn():
    """
    Returns a psycopg2 connection.
    cursor_factory=RealDictCursor means rows come back as dicts,
    so you can do row["supplier_id"] instead of row[0].
    """
    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn