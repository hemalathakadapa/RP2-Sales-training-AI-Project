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
    stage,
    chat_count
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
    Identity: {persona}, qualified in {qualification} with background in {subject}.

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
    
    4. If course_introduced is True AND stage != "closing":
       - Continue the discussion naturally. 
       - Ask only ONE new question at a time about: Duration, Projects, Internship, Placement, Certification, or Fees.
       - Never repeat a question.

    5. If stage == "closing":
       - You are now convinced. Do NOT ask new technical questions.
       - Act like a genuine student ready to join.
       - Ask about: Admission process, Enrollment, EMI, Scholarships, or Batch start dates.
       - Show buying intent (e.g., "I'd like to proceed", "Please help me with admission").

    --------------------------------------------------
    CONTEXT:
    {retrieved_text}

    HISTORY:
    {history_text}

    SALESPERSON SAYS:
    "{user_message}"

    Reply ONLY as {student_name}:
    """

    # 4. Attempt to call the LLM
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
            "response": "That sounds interesting. Could you tell me more about the next steps?",
            "student_name": student_name,
            "student_gender": student_gender
        }