import requests

BACKEND_URL = "https://ai-student-simulator-for-training-sales.onrender.com"

def get_ai_response(message: str, persona: str, course: str, session_id: str = "") -> dict:
    payload = {
        "message":    message,
        "persona":    persona,
        "course":     course,
        "session_id": session_id
    }
    response = requests.post(f"{BACKEND_URL}/chat/", json=payload)
    response.raise_for_status()
    return response.json()

def get_evaluation(session_id: str, mode: str = "recent") -> dict:
    """Get AI evaluation/feedback for a session"""
    response = requests.get(f"{BACKEND_URL}/feedback/evaluate/{session_id}", params={"mode": mode})
    response.raise_for_status()
    return response.json()

def reset_conversation(session_id: str) -> dict:
    """Clear conversation history for a session"""
    response = requests.post(f"{BACKEND_URL}/reset", params={"session_id": session_id})
    response.raise_for_status()
    return response.json()
 
 
def get_all_sessions() -> list:
    """Get all past sessions for admin dashboard"""
    response = requests.get(f"{BACKEND_URL}/feedback/sessions")
    response.raise_for_status()
    return response.json().get("sessions", [])
 
 
def get_session_conversation(session_id: str) -> list:
    """Get full conversation history for a session"""
    response = requests.get(f"{BACKEND_URL}/chat/history/{session_id}")
    response.raise_for_status()
    return response.json().get("history", [])

def rename_chat_session(session_id: str, title: str):

    response = requests.put(
        f"{BACKEND_URL}/session/rename/{session_id}",
        json={"title": title}
    )

    response.raise_for_status()

    return response.json()

def register_user(name, email, password):

    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password
        }
    )

    return response.json()

def login_user(email, password):

    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    return response.json()
