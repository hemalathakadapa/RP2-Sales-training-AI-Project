import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ✅ Call your Render backend — not Groq directly
BASE_URL = os.getenv("API_URL", "https://ai-student-simulator-for-training-sales.onrender.com")

def get_ai_response(message: str, persona: str, course: str, session_id: str = ""):
    try:
        response = requests.post(
            f"{BASE_URL}/chat/",
            json={
                "message":    message,
                "persona":    persona,
                "course":     course,
                "session_id": session_id
            },
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"error": str(e), "response": "Backend connection failed"}

def get_evaluation(session_id: str, mode: str = "full"):
    try:
        response = requests.get(
            f"{BASE_URL}/feedback/evaluate/{session_id}",
            params={"mode": mode},
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_final_feedback(conversation_history: str):
    return {"error": "Use get_evaluation instead"}

def reset_conversation(session_id: str):
    try:
        response = requests.post(
            f"{BASE_URL}/reset",
            params={"session_id": session_id},
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_all_sessions():
    try:
        response = requests.get(f"{BASE_URL}/feedback/sessions", timeout=10)
        return response.json().get("sessions", [])
    except Exception as e:
        return []

def get_session_conversation(session_id: str):
    try:
        response = requests.get(f"{BASE_URL}/chat/history/{session_id}", timeout=10)
        return response.json().get("history", [])
    except Exception as e:
        return []

def rename_chat_session(session_id: str, title: str):
    try:
        response = requests.put(
            f"{BASE_URL}/session/rename/{session_id}",
            json={"title": title},
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}
