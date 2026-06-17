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
        conversation_stage = get_conversation_stage(session_id)
        chat_count = len(conversation_history)

        # ✅ FIXED: Correctly indented "finished" check
        if conversation_stage == "finished":
            return {
                "response": "This practice session has ended successfully. Please start a new chat to practice again.",
                "session_id": session_id,
                "conversation_finished": True
            }

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

        # 7. Update Conversation Stage
        if conversation_stage == "greeting":
            update_conversation_stage(session_id, "waiting_for_rp2")

        elif conversation_stage == "waiting_for_rp2":
            if "rp2" in message.lower():
                update_conversation_stage(session_id, "waiting_for_course")

        elif conversation_stage == "waiting_for_course":
            if selected_course:
                update_conversation_stage(session_id, "course_discussion")

        elif conversation_stage == "closing":
    admission_keywords = [
        "admission", "enroll", "enrol", "registration", "register",
        "payment", "fees", "fee payment", "emi", "batch starts",
        "seat", "join now", "application form",
        "confirm my seat", "book my seat"
    ]

    if any(word in message.lower() for word in admission_keywords):
        update_conversation_stage(session_id, FINISHED)
        conversation_stage = FINISHED

        # 8. Generate voice
        audio_file = convert_text_to_speech(
            text=response_text,
            gender=student_gender
        )
        audio_url = f"/voice/audio/{audio_file}" if audio_file else None

        # ✅ FIXED: Ensure the return is outside the "if" logic but inside the "try" block
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