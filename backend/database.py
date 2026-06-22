
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from password_utils import hash_password, verify_password
from datetime import datetime
from zoneinfo import ZoneInfo
from b_config import DATABASE_URL

IST = ZoneInfo("Asia/Kolkata")

def ist_now():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

def create_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT
    )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id            SERIAL PRIMARY KEY,
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id    INTEGER,
            title TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id            SERIAL PRIMARY KEY,
            session_id    TEXT    NOT NULL,
            final_score   REAL,
            groq_score    REAL,
            keyword_score REAL,
            tone_score    REAL,
            summary       TEXT,
            timestamp     TEXT
        )
    """)

    conn.commit()

    # ── existing migrations ──
    migrations = [
        ("sessions",      "user_id INTEGER"),
        ("sessions",      "conversation_stage TEXT DEFAULT 'greeting'"),
        ("sessions",      "student_name TEXT"),
        ("sessions",      "student_gender TEXT"),
        ("conversations", "qualification TEXT DEFAULT ''"),
        ("conversations", "subject TEXT DEFAULT ''"),
        # ── NEW: branch support ──
        ("users",         "branch TEXT DEFAULT ''"),
        ("admins",        "branch TEXT DEFAULT 'All'"),
        ("admins",        "admin_role TEXT DEFAULT 'super_admin'"),
    ]

    for table, col_def in migrations:
        col_name = col_def.split()[0]
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {' '.join(col_def.split()[1:])}")
            conn.commit()
            print(f"✅ Migrated: added {col_name} to {table}")
        except Exception:
            conn.rollback()

    conn.close()
    print("✅ Database tables ready")

# ── Sessions ──

def create_session(session_id: str, title: str, user_id: int):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        INSERT INTO sessions (session_id, user_id, title, conversation_stage, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (session_id) DO NOTHING
    """, (session_id, user_id, title, "greeting", ist_now(), ist_now()))
    conn.commit()
    conn.close()

def update_session_timestamp(session_id: str):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("UPDATE sessions SET updated_at = %s WHERE session_id = %s", (ist_now(), session_id))
    conn.commit()
    conn.close()

def rename_session(session_id: str, new_title: str):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("UPDATE sessions SET title = %s WHERE session_id = %s", (new_title, session_id))
    conn.commit()
    conn.close()

def get_user_sessions(user_id: int):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT s.session_id, s.title, s.created_at, s.updated_at, c.persona, c.course
        FROM sessions s
        LEFT JOIN LATERAL (
            SELECT persona, course FROM conversations
            WHERE conversations.session_id = s.session_id
            ORDER BY id ASC LIMIT 1
        ) c ON true
        WHERE s.user_id = %s
        ORDER BY s.updated_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "session_id": row["session_id"],
            "title":      row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "persona":    row["persona"] or "N/A",
            "course":     row["course"]  or "N/A"
        }
        for row in rows
    ]

def session_belongs_to_user(session_id: str, user_id: int):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT 1 FROM sessions WHERE session_id = %s AND user_id = %s", (session_id, user_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def delete_session_completely(session_id: str):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("DELETE FROM conversations WHERE session_id = %s", (session_id,))
        cursor.execute("DELETE FROM feedback      WHERE session_id = %s", (session_id,))
        cursor.execute("DELETE FROM sessions      WHERE session_id = %s", (session_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("Delete failed:", e)
        return False
    finally:
        conn.close()

# ── Conversation stage ──

def get_conversation_stage(session_id: str):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT conversation_stage FROM sessions WHERE session_id = %s", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return row["conversation_stage"] if row else "greeting"

def update_conversation_stage(session_id: str, stage: str):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "UPDATE sessions SET conversation_stage=%s, updated_at=%s WHERE session_id=%s",
        (stage, ist_now(), session_id)
    )
    conn.commit()
    conn.close()

def save_student_identity(session_id: str, student_name: str, student_gender: str):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "UPDATE sessions SET student_name=%s, student_gender=%s WHERE session_id=%s",
        (student_name, student_gender, session_id)
    )
    conn.commit()
    conn.close()

def get_student_identity(session_id: str):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT student_name, student_gender FROM sessions WHERE session_id=%s", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["student_name"], row["student_gender"]
    return None, None

# ── Conversations ──

def get_conversation(session_id: str, limit: int = 999):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT salesperson, student, persona, course, timestamp
        FROM conversations WHERE session_id = %s
        ORDER BY id DESC LIMIT %s
    """, (session_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [
        {"salesperson": r["salesperson"], "student": r["student"],
         "persona": r["persona"], "course": r["course"], "timestamp": r["timestamp"]}
        for r in reversed(rows)
    ]

def save_conversation(session_id, salesperson_msg, student_msg,
                      persona="", course="", qualification="", subject=""):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        INSERT INTO conversations
            (session_id, salesperson, student, persona, course, qualification, subject, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (session_id, salesperson_msg, student_msg, persona, course, qualification, subject, ist_now()))
    conn.commit()
    conn.close()

def clear_conversation(session_id: str):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("DELETE FROM conversations WHERE session_id = %s", (session_id,))
    conn.commit()
    conn.close()

# ── Feedback ──

def save_feedback(session_id, score, groq_score=0, keyword_score=0, tone_score=0, summary=""):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        INSERT INTO feedback
            (session_id, final_score, groq_score, keyword_score, tone_score, summary, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (session_id, score, groq_score, keyword_score, tone_score, summary, ist_now()))
    conn.commit()
    conn.close()

def get_feedback_history(session_id: str):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT final_score, groq_score, keyword_score, tone_score, summary, timestamp
        FROM feedback WHERE session_id = %s ORDER BY id DESC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Users ──

def create_user(name, email, password, branch=""):
    """branch is saved from the login/signup branch dropdown."""
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    hashed = hash_password(password)
    try:
        cursor.execute("""
            INSERT INTO users (name, email, password, branch, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (name, email, hashed, branch, ist_now()))
        new_id = cursor.fetchone()["id"]
        conn.commit()
        print("USER SAVED, ID =", new_id)
        return new_id
    except Exception as e:
        conn.rollback()
        print("INSERT FAILED:", e)
        raise
    finally:
        conn.close()

def get_user(email, password):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    conn.close()
    if not user or not verify_password(password, user["password"]):
        return None
    return user

def update_password(email, new_password):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hash_password(new_password), email))
    conn.commit()
    updated = cursor.rowcount
    conn.close()
    return updated > 0

def update_user_branch(user_id: int, branch: str):
    """Called on every login so branch is always current."""
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("UPDATE users SET branch = %s WHERE id = %s", (branch, user_id))
    conn.commit()
    updated = cursor.rowcount
    conn.close()
    return updated > 0

def get_user_by_id(user_id: int):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_users():
    """Now includes branch — used by Admin Dashboard."""
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id, name, email, branch FROM users ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r["id"], "name": r["name"], "email": r["email"], "branch": r["branch"] or ""}
        for r in rows
    ]

def get_all_sessions_admin():
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT s.session_id, s.title, s.created_at, s.updated_at,
               u.id as user_id, u.name, u.email, u.branch
        FROM sessions s
        LEFT JOIN users u ON s.user_id = u.id
        ORDER BY s.updated_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_user_dashboard(user_id: int):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT s.session_id, f.final_score
        FROM feedback f
        JOIN sessions s ON f.session_id = s.session_id
        WHERE s.user_id = %s
        ORDER BY f.timestamp ASC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    performance, scores = [], []
    for row in rows:
        score = row["final_score"]
        if score is not None:
            scores.append(score)
            performance.append({
                "session_id":   row["session_id"],
                "growth_score": round(sum(scores) / len(scores), 1)
            })
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    return {"average_score": avg_score, "sessions_completed": len(scores), "performance": performance}

def get_course_metrics(user_id: int):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT c.course,
               COUNT(DISTINCT s.session_id) AS total_sessions,
               ROUND(AVG(f.final_score)::numeric, 1) AS avg_score
        FROM sessions s
        JOIN conversations c ON s.session_id = c.session_id
        LEFT JOIN feedback f ON s.session_id = f.session_id
        WHERE s.user_id = %s AND c.course != ''
        GROUP BY c.course
        ORDER BY total_sessions DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"course": r["course"], "sessions": r["total_sessions"], "average_score": r["avg_score"] or 0} for r in rows]

# ── Admins ──

def create_admin(name, email, password, branch="All", admin_role="super_admin"):
    """branch: 'Bangalore'/'Cochin'/'Calicut'/'All'
       admin_role: 'branch_admin' or 'super_admin'"""
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    hashed = hash_password(password)
    try:
        cursor.execute("""
            INSERT INTO admins (name, email, password, branch, admin_role, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (name, email, hashed, branch, admin_role, ist_now()))
        new_id = cursor.fetchone()["id"]
        conn.commit()
        print("ADMIN SAVED, ID =", new_id)
        return new_id
    except Exception as e:
        conn.rollback()
        print("ADMIN INSERT FAILED:", e)
        raise
    finally:
        conn.close()

def get_admin(email, password):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
    admin = cursor.fetchone()
    conn.close()
    if not admin or not verify_password(password, admin["password"]):
        return None
    return admin

def update_admin_password(email, new_password):
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("UPDATE admins SET password = %s WHERE email = %s", (hash_password(new_password), email))
    conn.commit()
    updated = cursor.rowcount
    conn.close()
    return updated > 0