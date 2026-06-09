import sqlite3
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from b_config import DB_PATH

IST = ZoneInfo("Asia/Kolkata")

def ist_now():
    """Return current IST time as string"""
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

def create_connection():
    """Create and return a database connection"""
    print("DB PATH =", os.path.abspath(DB_PATH))
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row  
    return conn

def create_tables():
    """Create all required tables if they don't exist"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT
    )
    """)

    # ✅ Conversations table with all needed columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    TEXT    NOT NULL,      
            salesperson   TEXT    NOT NULL,
            student       TEXT    NOT NULL,
            persona       TEXT    DEFAULT '',
            course        TEXT    DEFAULT '',
            qualification TEXT    DEFAULT '',
            subject       TEXT    DEFAULT '',
            timestamp     TEXT    
        )
    """)

    # ✅ Session metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id    INTEGER,
            title TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # ✅ Feedback table for evaluation results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    TEXT    NOT NULL,
            final_score   REAL,
            groq_score  REAL,
            keyword_score REAL,
            tone_score    REAL,
            summary       TEXT,
            timestamp     TEXT    
        )
    """)

    try:
        cursor.execute("ALTER TABLE sessions ADD COLUMN user_id INTEGER")
        conn.commit()
        print("✅ Migrated: added user_id to sessions")
    except Exception:
        pass  # column already exists, ignore

    for col in ["qualification", "subject"]:
        try:
            cursor.execute(f"ALTER TABLE conversations ADD COLUMN {col} TEXT DEFAULT ''")
            conn.commit()
            print(f"✅ Migrated: added {col} to conversations")
        except Exception:
            pass  # column already exists

    conn.commit()
    conn.close()
    print("✅ Database tables ready")

def create_session(session_id: str, title: str, user_id: int):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO sessions
        (session_id, user_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        session_id, user_id, title, ist_now(), ist_now()))

    conn.commit()
    conn.close()

def update_session_timestamp(session_id: str):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sessions
        SET updated_at = ?
        WHERE session_id = ?
    """, (ist_now(), session_id))

    conn.commit()
    conn.close()

def rename_session(session_id: str, new_title: str):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sessions
        SET title = ?
        WHERE session_id = ?
    """, (new_title, session_id))

    conn.commit()
    conn.close()

def get_user_sessions(user_id: int):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM sessions
        WHERE user_id = ?
        ORDER BY updated_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "session_id": row["session_id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
        for row in rows
    ]
                                                                                                                                                                                                                                                                                                                                                                                                                                                       

def get_conversation(session_id: str, limit: int = 999):
    """Get last N conversation turns"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT salesperson, student, persona, course, timestamp
        FROM conversations
        WHERE session_id = ?
        ORDER BY id DESC 
        LIMIT ?
    """, (session_id, limit,))

    rows = cursor.fetchall()
    conn.close()

    # ✅ Reverse to get chronological order
    history = [
        {"salesperson": row["salesperson"], "student": row["student"], "persona": row["persona"], "course": row["course"], "timestamp":   row["timestamp"]}
        for row in reversed(rows)
    ]
    return history


def save_conversation(
    session_id: str,
    salesperson_msg: str,
    student_msg: str,
    persona: str = "",
    course: str = "",
    qualification: str = "",
    subject: str = ""
):
    """Save one conversation turn to database"""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO conversations (session_id, salesperson, student, persona, course, qualification, subject, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_id, salesperson_msg, student_msg, persona, course, qualification, subject, ist_now()))

    conn.commit()
    conn.close()


def clear_conversation(session_id: str):
    """Delete all conversation history"""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM conversations WHERE session_id = ?",
        (session_id,)
    )

    conn.commit()
    conn.close()
    print("🗑️ Conversation history cleared")


def save_feedback(session_id: str, score: float, groq_score: float = 0, keyword_score: float = 0, tone_score: float = 0, summary: str = ""):
    """Save evaluation result to database"""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO feedback (session_id, final_score, groq_score, keyword_score, tone_score, summary, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, score, groq_score, keyword_score, tone_score, summary, ist_now()))

    conn.commit()
    conn.close()


def get_feedback_history(session_id: str):
    """Get all past feedback records"""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT final_score, groq_score, keyword_score, tone_score, summary, timestamp
        FROM feedback
        WHERE session_id = ?
        ORDER BY id DESC
    """, (session_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "final_score":   row["final_score"],
            "groq_score":  row["groq_score"],
            "keyword_score": row["keyword_score"],
            "tone_score":    row["tone_score"],
            "summary": row["summary"],
            "timestamp": row["timestamp"]
        }
        for row in rows
    ]

def create_user(name, email, password):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users
            (name, email, password, created_at)
            VALUES (?, ?, ?, ?)
        """, (name, email, password, ist_now()))

        conn.commit()
        print("USER SAVED")
        print("ID =", cursor.lastrowid)

    except Exception as e:
        print("INSERT FAILED:", e)

    finally:
        conn.close()

def get_user(email, password):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE email = ?
        AND password = ?
    """, (
        email,
        password
    ))

    user = cursor.fetchone()

    conn.close()

    return user

def update_password(email, new_password):

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET password = ?
        WHERE email = ?
    """, (
        new_password,
        email
    ))

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    return updated > 0

def session_belongs_to_user(session_id: str, user_id: int):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1
        FROM sessions
        WHERE session_id = ?
        AND user_id = ?
    """, (session_id, user_id))

    result = cursor.fetchone()
    conn.close()

    return result is not None

def get_all_users():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, email
        FROM users
        ORDER BY name
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"]
        }
        for row in rows
    ]

def get_user_by_id(user_id: int):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None

def get_all_sessions_admin():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.session_id,
            s.title,
            s.created_at,
            s.updated_at,
            u.id as user_id,
            u.name,
            u.email
        FROM sessions s
        LEFT JOIN users u
        ON s.user_id = u.id
        ORDER BY s.updated_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_user_dashboard(user_id: int):

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            s.session_id,
            f.final_score
        FROM feedback f
        JOIN sessions s
        ON f.session_id = s.session_id
        WHERE s.user_id = ?
        ORDER BY f.timestamp ASC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    performance = []
    scores = []

    for row in rows:
        score = row["final_score"]
        if scores is not None:
            scores.append(score)
            running_total = 0
            running_total += score
            growth_score = round(
                running_total / len(scores),
                1
            )

            performance.append({
                "session_id": row["session_id"],
                "growth_score": growth_score
            })    

    avg_score = (
        round(sum(scores) / len(scores), 1)
        if scores else 0
    )

    return {
        "average_score": avg_score,
        "sessions_completed": len(scores),
        "performance": performance
    }

def get_course_metrics(user_id: int):

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.course,
            COUNT(DISTINCT s.session_id) AS total_sessions,
            ROUND(AVG(f.final_score), 1) AS avg_score
        FROM sessions s
        JOIN conversations c
            ON s.session_id = c.session_id
        LEFT JOIN feedback f
            ON s.session_id = f.session_id
        WHERE s.user_id = ?
          AND c.course != ''
        GROUP BY c.course
        ORDER BY total_sessions DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "course": row["course"],
            "sessions": row["total_sessions"],
            "average_score": row["avg_score"] or 0
        }
        for row in rows
    ]