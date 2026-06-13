from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from b_config import USE_LLM
from database import (create_session, get_user_dashboard, get_course_metrics)
import random
import string
from ai_logic.chat_stage import (
    should_start_closing,
    CLOSING
)

def generate_session_id():
    chars = string.ascii_uppercase + string.digits
    code = "".join(random.choices(chars, k=5))
    return f"RP2-{code}"

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    persona: str = ""
    course: str = ""
    qualification: str = ""
    subject: str = ""
    session_id: str = ""
    user_id: int = None

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
        from database import (
            get_conversation, 
            save_conversation, 
            update_session_timestamp, 
            get_conversation_stage, 
            update_conversation_stage
        )
        from ai_logic.rag import search
        from ai_logic.llm import get_llm_response
        from ai_logic.chatbot import get_response
        from text_to_speech import convert_text_to_speech

        # 1. Extract fields
        message = user_message.message
        selected_persona = user_message.persona
        selected_course = user_message.course
        selected_qualification = user_message.qualification
        selected_subject = user_message.subject

        # 2. Session Management
        if not user_message.session_id:
            session_id = generate_session_id()
            title = message[:30]
            create_session(session_id, title, user_message.user_id)
        else:
            session_id = user_message.session_id

        if not message:
            return {"error": "Message cannot be empty"}
        if not selected_course:
            return {"error": "Course must be selected"}

        # 3. History and Stage logic
        conversation_history = get_conversation(session_id)
        chat_count = len(conversation_history)
        conversation_stage = get_conversation_stage(session_id)

        # Automatically switch to closing stage if threshold met
        if should_start_closing(chat_count) and conversation_stage != CLOSING:
            update_conversation_stage(session_id, CLOSING)
            conversation_stage = CLOSING
        
        # 4. Retrieval (RAG)
        retrieved_text = ""
        search_results = search(message)
        if search_results and len(search_results) > 0:
            retrieved_text = search_results[0].get("answer", "")

        # 5. Generate Response
        response_text = ""
        student_name = "Student"
        student_gender = "unknown"

        if USE_LLM:
            llm_data = get_llm_response(
                user_message=message,
                retrieved_text=f"Course: {selected_course}\n{retrieved_text}",
                persona=selected_persona,
                qualification=selected_qualification,
                subject=selected_subject,
                history=conversation_history,
                stage=conversation_stage,
                chat_count=chat_count
            )
            response_text = llm_data.get("response", "")
            student_name = llm_data.get("student_name", "")
            student_gender = llm_data.get("student_gender", "")
        else:
            if retrieved_text:
                response_text = fallback_response(message, selected_course, retrieved_text)
            else:
                response_text = get_response(
                    user_message=message,
                    persona=selected_persona,
                    history=conversation_history,
                    session_id=session_id,
                    course=selected_course
                )

        # 6. Save Conversation
        save_conversation(
            session_id=session_id,
            salesperson_msg=message,
            student_msg=response_text,
            persona=selected_persona,
            course=selected_course,
            qualification=selected_qualification,
            subject=selected_subject
        )
        update_session_timestamp(session_id)

        # 7. Update Conversation Stage (Fixing the Elif chain indentation)
        if conversation_stage == "greeting":
            update_conversation_stage(session_id, "waiting_for_rp2")

        elif conversation_stage == "waiting_for_rp2":
            if "rp2" in message.lower():
                update_conversation_stage(session_id, "waiting_for_course")

        elif conversation_stage == "waiting_for_course":
            if selected_course:
                update_conversation_stage(session_id, "course_discussion")

        elif conversation_stage == "closing":
            salesperson_lower = message.lower()
            admission_keywords = [
                "admission", "enroll", "enrol", "registration", "register",
                "payment", "fees", "fee payment", "emi", "batch starts",
                "seat", "join now", "application form"
            ]
            if any(word in salesperson_lower for word in admission_keywords):
                update_conversation_stage(session_id, "finished")

        # 8. Generate voice
        audio_file = convert_text_to_speech(text=response_text)
        audio_url = f"/voice/audio/{audio_file}" if audio_file else None

        return {
            "response": response_text,
            "audio_url": audio_url,
            "session_id": session_id,
            "student_name": student_name,
            "student_gender": student_gender,
            "stage": conversation_stage
        }

    except Exception as e:
        print("Error:", e)
        return {"error": f"Something went wrong: {str(e)}"}

# --- Admin/Dashboard endpoints ---
@router.get("/history/{session_id}")
def get_chat_history(session_id: str, user_id: int):
    try:
        from database import (get_conversation, session_belongs_to_user)
        if not session_belongs_to_user(session_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        history = get_conversation(session_id=session_id, limit=999)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
def get_sessions(user_id: int):
    from database import get_user_sessions
    return get_user_sessions(user_id)

@router.get("/dashboard")
def dashboard(user_id: int):
    return get_user_dashboard(user_id)

@router.get("/course-metrics")
def course_metrics(user_id: int):
    return {"course_metrics": get_course_metrics(user_id)}

@router.get("/admin/users")
def admin_users():
    from database import get_all_users
    return get_all_users()
