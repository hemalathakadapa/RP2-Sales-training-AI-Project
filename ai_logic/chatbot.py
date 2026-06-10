import random

# ----------------------------------
# Conversation State
# ----------------------------------

conversation_state = {
    "stage": "greeting"
}

# ----------------------------------
# Student Personas
# ----------------------------------

student_personas = {

    "confused_student": [
        "I'm still confused about my career.",
        "Can you help me choose the right course?"
    ],

    "it_student": [
        "I'm from an IT background.",
        "I already know some programming."
    ],

    "non_it_student": [
        "I'm from a non-technical background.",
        "I don't know coding."
    ],

    "career_switcher": [
        "I'm planning to switch my career.",
        "Can I move into IT?"
    ]

}


def detect_persona(message):

    message = message.lower()

    if "it" in message or "developer" in message:
        return "it_student"

    elif "commerce" in message or "non technical" in message:
        return "non_it_student"

    elif "career change" in message or "switch" in message:
        return "career_switcher"

    return "confused_student"


# ----------------------------------
# Main Chatbot Logic
# ----------------------------------

def get_response(user_message,
                 persona=None,
                 session_id=None,
                 course=None,
                 history=None):

    msg = user_message.lower()

    # ----------------------------------
    # STEP 1
    # Greeting
    # ----------------------------------

   if conversation_state["stage"] == "rp2":

    rp2_keywords = [
        "rp2",
        "training",
        "academy",
        "institute",
        "company",
        "education",
        "platform",
        "learning"
    ]

    if any(word in msg for word in rp2_keywords):

        conversation_state["stage"] = "course"

        return (
            "Thank you for explaining RP2. "
            "Which course are you introducing today?"
        )

    return (
        "I'm still not very clear about RP2. "
        "Could you tell me a little more about what RP2 does?"
    )

    # ----------------------------------
    # STEP 2
    # Learn RP2
    # ----------------------------------

    if conversation_state["stage"] == "rp2":

        conversation_state["stage"] = "course"

        return (
            "Thank you for explaining RP2. "
            "Which course are you introducing today?"
        )

    # ----------------------------------
    # STEP 3
    # Detect Course
    # ----------------------------------

    if conversation_state["stage"] == "course":

        courses = [

            "data science",

            "data analytics",

            "agentic ai",

            "artificial intelligence",

            "cyber security",

            "cybersecurity",

            "machine learning"

        ]

        for c in courses:

            if c in msg:

                conversation_state["course"] = c

                conversation_state["stage"] = "details"

                return (
                    f"{c.title()} sounds interesting. "
                    "Could you explain this course in detail?"
                )

        return (
            "Could you tell me which course you're introducing today?"
        )

    # ----------------------------------
    # STEP 4
    # Ask Questions
    # ----------------------------------

    if conversation_state["stage"] == "details":

        questions = [

            "What topics are covered in the syllabus?",

            "How long is the course?",

            "Will I work on real-world projects?",

            "Who are the trainers?",

            "Do you provide placement assistance?",

            "Will I receive a certificate?",

            "What are the course fees?",

            "Is this course suitable for beginners?"

        ]

        return random.choice(questions)

    # ----------------------------------
    # Fallback
    # ----------------------------------

    detected = detect_persona(user_message)

    return random.choice(student_personas[detected])


# ----------------------------------
# Wrapper
# ----------------------------------

def chatbot_response(message):

    return get_response(message)
