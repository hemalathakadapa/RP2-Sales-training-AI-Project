import random

student_personas = {

    "confused_student": [
        "I don't know which course is better for my future.",
        "I'm confused between AI and Data Science.",
        "Will I get placement after this course?",
        "Is coding difficult?",
        "I am from commerce background. Can I study AI?",
        "My parents are asking whether this field has future scope."
    ],

    "it_student": [
        "I'm from IT background.",
        "Which course has highest salary package?",
        "Should I choose AI or Cybersecurity?",
        "Which field is better for future jobs?",
        "I already know basic coding."
    ],

    "non_it_student": [
        "I don't know coding.",
        "Can non-technical students join?",
        "Will it be difficult for beginners?",
        "Which course is easiest to start?",
        "Can I get job without coding knowledge?"
    ],

    "career_switcher": [
        "I'm planning career change.",
        "Can I switch from mechanical to AI?",
        "How long does it take to get job ready?",
        "Do companies accept non-IT students?"
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


def get_response(user_message, persona =None, session_id=None, course= None, history=None):

    detected = detect_persona(user_message)

    responses = student_personas[detected]

    # dynamic reactions

    if "salary" in user_message.lower():
        return "What salary can I expect after completing the course?"

    if "placement" in user_message.lower():
        return "Do RP2 provide placement support?"

    if "ai" in user_message.lower():
        return "I heard AI needs strong coding skills. Is that true?"

    if "data science" in user_message.lower():
        return "Is Data Science easier than AI?"

    if "cybersecurity" in user_message.lower():
        return "Does Cybersecurity need programming knowledge?"

    return random.choice(responses)
def chatbot_response(message):
    return get_response(message)
