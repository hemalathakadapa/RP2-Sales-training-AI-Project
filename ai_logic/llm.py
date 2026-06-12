import os
import random
from dotenv import load_dotenv
from groq import Groq

# Constants
MALE_NAMES = ["Rahul", "Arjun", "Karthik", "Aditya", "Vikram", "Rohan"]
FEMALE_NAMES = ["Aisha", "Priya", "Ananya", "Meera"]
ALL_NAMES = MALE_NAMES + FEMALE_NAMES

# Initial selection
student_name = random.choice(ALL_NAMES)
student_gender = "female" if student_name in FEMALE_NAMES else "male"

load_dotenv()

def get_client():
    key = os.getenv("GROQ_API_KEY", "")
    if key:
        return Groq(api_key=key)
    return None

client = get_client()
GROQ_MODEL = "llama-3.1-8b-instant"

if client:
    print("✅ LLM ready")
else:
    print("⚠️ No API key found")

def get_llm_response(
    user_message,
    retrieved_text,
    persona,
    qualification,
    subject,
    history,
    stage
):
    if client is None:
        return {"response": "I'm exploring course options. Can you tell me more?", "student_name": student_name}

    # 1. Build history text from the list of dictionaries
    history_text = ""
    for turn in history[-5:]:
        salesperson = turn.get("salesperson", "")
        student = turn.get("student", "")
        history_text += f"Salesperson: {salesperson}\nStudent: {student}\n\n"

    # 2. Determine conversation state logic
    history_lower = history_text.lower()
    conversation_started = len(history) > 0
    
    rp2_explained = (
        "rp2" in history_lower and
        any(word in history_lower for word in ["institute", "academy", "training", "center"])
    )

    course_keywords = ["data science", "agentic ai", "artificial intelligence", "data analytics", "machine learning"]
    course_introduced = any(course in history_lower for course in course_keywords)

    # 3. Construct the Master Prompt
    MASTER_PROMPT = f"""
    You are {student_name}, a prospective student speaking with an RP2 sales counselor.
    Gender: {student_gender}

    Always maintain this identity. Never change your name.

    YOUR GOAL:
    Behave exactly like a real student. 

    --------------------------------------------------
    CONVERSATION FLOW (STRICT)
    --------------------------------------------------
    STAGE: {stage}

    1. If stage is "greeting" or history is empty:
       - Reply: "Hi! Thank you for welcoming me. My name is {student_name}. It's nice to meet you. Before we begin, could you tell me a little about RP2?"
    
    2. If rp2_explained is False:
       - Ask ONLY about RP2. Do NOT mention courses.
    
    3. If rp2_explained is True and course_introduced is False:
       - Ask: "Thank you for explaining RP2. Which course are you introducing today?"
    
    4. If course_introduced is True:
       - Ask ONE specific question at a time about: syllabus, duration, projects, trainers, internship, placement, or fees.

    --------------------------------------------------
    IMPORTANT RULES:
    - Never assume the course. Wait for the counselor to name it.
    - Ask ONE question at a time.
    - Never behave like an AI or ChatGPT. Keep responses short and human-like.
    - Do NOT use the course context below until the counselor has named the course.

    --------------------------------------------------
    STUDENT PROFILE:
    Persona: {persona}
    Qualification: {qualification}
    Background: {subject}

    COURSE CONTEXT (For your reference once named):
    {retrieved_text}

    CONVERSATION HISTORY:
    {history_text}

    Salesperson: "{user_message}"

    Reply ONLY as {student_name}:
    """

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": MASTER_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=400,
        )

        llm_content = response.choices[0].message.content.strip()
        
        return {
            "response": llm_content,
            "student_name": student_name,
            "student_gender": student_gender
        }

    except Exception as e:
        print("LLM ERROR:", e)
        return {
            "response": f"I'm sorry, I'm having trouble connecting. Could you repeat that?",
            "student_name": student_name,
            "student_gender": student_gender
        }
