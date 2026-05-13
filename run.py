from ai_logic.chatbot import get_response
from ai_logic.voice import speak, listen

history = []

print("🎤 Voice AI started (type 'exit' to stop)\n")

while True:

    user_input = listen()

    if not user_input:
        continue

    if user_input.lower() == "exit":
        speak("Goodbye!")
        break

    response = get_response(user_input, "student", history)

    history.append(("user", user_input))
    history.append(("ai", response))

    speak(response)