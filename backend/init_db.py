import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# ✅ EXPLICITLY load .env from current directory
load_dotenv(dotenv_path=".env")

DATABASE_URL = os.getenv("DATABASE_URL")

# ✅ DEBUG: Print to verify it loaded
print(f"🔍 DATABASE_URL loaded: {DATABASE_URL[:50]}..." if DATABASE_URL else "❌ DATABASE_URL not found!")

def create_tables():
    if not DATABASE_URL:
        raise ValueError("❌ DATABASE_URL environment variable not set!")
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT
    )
    """)

    # SESSIONS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        user_id INTEGER,
        title TEXT,
        conversation_stage TEXT DEFAULT 'greeting',
        created_at TEXT,
        updated_at TEXT
    )
    """)

    # CONVERSATIONS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id SERIAL PRIMARY KEY,
        session_id TEXT,
        salesperson TEXT,
        student TEXT,
        persona TEXT DEFAULT '',
        course TEXT DEFAULT '',
        qualification TEXT DEFAULT '',
        subject TEXT DEFAULT '',
        timestamp TEXT
    )
    """)

    # FEEDBACK
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id SERIAL PRIMARY KEY,
        session_id TEXT,
        final_score REAL,
        groq_score REAL,
        keyword_score REAL,
        tone_score REAL,
        summary TEXT,
        timestamp TEXT
    )
    """)

    # ADMINS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()
    print("✅ All tables created successfully in PostgreSQL")

if __name__ == "__main__":
    create_tables()
