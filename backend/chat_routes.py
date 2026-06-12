from fastapi import APIRouter
from pydantic import BaseModel
from b_config import USE_LLM
from database import (create_session, get_user_dashboard, get_course_metrics)
from fastapi import HTTPException
import random
import string

def generate_session_id():
    chars = string.ascii_uppercase + string.digits
    code  = "".join(random.choices(chars, k=5))
    return f"RP2-{code}"

router = APIRouter()

class ChatRequest(BaseModel):
    message:    str
    persona:    str = ""
    course:     str = ""
    qualification: str = ""
    subject: str = ""
    session_id: str = ""
    user_id:    int = None


def fallback_response(user_input, course, rag_text=None):
    if rag_text:
        return f"{rag_text} (Let me know if you want more details!)"
    return (
        f"Thanks for your question about the {course} course! "
        "This program covers everything step-by-step with practical examples. "
        "Would you like to know about syllabus, tools, or career opportunities?"
    )


@router.post("/")                          
def chat(user_message: ChatRequest):
    try:
        
        from database import (get_conversation, save_conversation, update_session_timestamp, get_conversation_stage, update_conversation_stage)
        from ai_logic.rag import search
        from ai_logic.llm import get_llm_response
        from ai_logic.chatbot import get_response
        from text_to_speech import convert_text_to_speech

        # ✅ Extract fields
        message          = user_message.message
        selected_persona = user_message.persona
        selected_course  = user_message.course
        selected_qualification = user_message.qualification
        selected_subject       = user_message.subject

        # ✅ Create NEW session if first chat
        if not user_message.session_id:
            session_id = generate_session_id()
            title = message[:30]
            create_session(session_id, title, user_message.user_id)
        else:
            session_id = user_message.session_id

        # ✅ Validate inputs
        if not message:
            return {"error": "Message cannot be empty"}
        if not selected_course:
            return {"error": "Course must be selected"}

        # ✅ Get THIS student's history
        conversation_history = get_conversation(session_id)
        conversation_stage = get_conversation_stage(session_id)
        print("========== HISTORY ==========")
        print(conversation_history)
        print("=============================")
    
        # 🔍 RAG search
        retrieved_text = search(message)
        student_gender = None
        student_name = None

        if retrieved_text and len(retrieved_text) > 0:
            top_result     = retrieved_text[0]
            retrieved_text = top_result.get("answer", "")

            if USE_LLM:
                response = get_llm_response(
                    user_message=message,
                    retrieved_text=f"Course: {selected_course}\n{retrieved_text}",
                    persona=selected_persona,
                    qualification=selected_qualification,
                    subject=selected_subject,
                    history=conversation_history,
                    stage=conversation_stage
                )

                response_text = response["response"]
                student_name = response["student_name"]
                student_gender = response["student_gender"]
            else:
                response_text = fallback_response(message,selected_course,retrieved_text)
        else:
            response_text = get_response(
                 user_message=message,
                 persona=selected_persona,
                 history=conversation_history,
                 session_id=session_id,
                 course=selected_course
            )

        # ✅ Save THIS student's conversation
        save_conversation(
            session_id      = session_id,
            salesperson_msg = message,
            student_msg     = response_text,
            persona         = selected_persona,
            course          = selected_course,
            qualification   = selected_qualification,
            subject         = selected_subject
        )
        update_session_timestamp(session_id)

        # Update conversation stage
        if conversation_stage == "greeting":
            update_conversation_stage(session_id, "waiting_for_rp2")

        elif conversation_stage == "waiting_for_rp2":
            if "rp2" in message.lower():
                update_conversation_stage(session_id, "waiting_for_course")

        elif conversation_stage == "waiting_for_course":
            if selected_course:
                update_conversation_stage(session_id, "course_discussion")

        # 🔊 Generate voice
        audio_file = convert_text_to_speech(text=response_text, gender=student_gender)
        audio_url  = f"/voice/audio/{audio_file}" if audio_file else None

        # ✅ Return response + session_id back to frontend
        return {
            "response":   response_text,
            "audio_url":  audio_url,
            "session_id": session_id
        }

    except Exception as e:
        print("Error:", e)
        return {"error": "Something went wrong in the backend"}


@router.get("/history/{session_id}")
def get_chat_history(session_id: str, user_id: int):
    try:
        from database import (
            get_conversation,
            session_belongs_to_user
        )

        if not session_belongs_to_user(session_id, user_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

        history = get_conversation(
            session_id=session_id,
            limit=999
        )

        return {
            "session_id": session_id,
            "history": history
        }

    except HTTPException:
        raise

    except Exception as e:
        print("History Error:", e)
        raise HTTPException(
            status_code=500,
            detail="Could not fetch history"
        )
    
@router.get("/sessions")
def get_sessions(user_id: int):
    from database import get_user_sessions
    return get_user_sessions(user_id)

@router.get("/admin/users")
def admin_users():
    from database import get_all_users
    return get_all_users()

@router.get("/admin/user-sessions")
def admin_user_sessions(user_id: int):
    from database import get_user_sessions
    return get_user_sessions(user_id)

@router.get("/admin/history/{session_id}")
def admin_history(session_id: str):
    from database import get_conversation
    history = get_conversation(session_id=session_id, limit=999)
    return {"session_id": session_id, "history": history}

@router.get("/dashboard")
def dashboard(user_id: int):
    dashboard_data = get_user_dashboard(user_id)
    return dashboard_data

@router.get("/course-metrics")
def course_metrics(user_id: int):
    return {"course_metrics": get_course_metrics(user_id)}
