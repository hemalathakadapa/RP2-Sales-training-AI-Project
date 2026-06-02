import requests
import os
import sys

BACKEND_URL = "https://ai-student-simulator-for-training-sales.onrender.com"

abs_path = os.path.dirname(os.path.abspath(__file__))
if abs_path not in sys.path:
    sys.path.insert(0, abs_path)

# =========================================================
# 2. STANDARD & THIRD-PARTY IMPORTS
# =========================================================
import streamlit as st
import json
import datetime
import base64
from streamlit_mic_recorder import speech_to_text

# =========================================================
# 3. LOCAL PROJECT IMPORTS (NOW THEY WILL WORK PERFECTLY)
# =========================================================
import importlib.util, os

_api_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "services", "api_client.py")
_spec = importlib.util.spec_from_file_location("api_client", _api_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

get_ai_response = _mod.get_ai_response
get_final_feedback = _mod.get_final_feedback

_pc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "persona_config.py")
_spec2 = importlib.util.spec_from_file_location("persona_config", _pc_path)
_mod2 = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(_mod2)

PERSONAS = _mod2.PERSONAS
COURSES = _mod2.COURSES


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="RP2 AI Sales Trainer",
    page_icon="🛡️",
    layout="wide"
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>
/* BACKGROUND */
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364) !important;
}

/* MAIN CONTAINER */
.block-container {
    padding: 2rem 3rem !important;
    background: transparent !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: #0b1220 !important;
}

/* TEXT */
h1, h2, h3, h4, h5, h6, p, label {
    color: white !important;
}

/* INPUTS */
input, textarea {
    background-color: white !important;
    color: black !important;
    border-radius: 10px !important;
}

/* CHAT BOX */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    padding: 10px !important;
}

/* BUTTON */
.stButton > button {
    background: linear-gradient(90deg, #4facfe, #00f2fe) !important;
    color: black !important;
    font-weight: bold !important;
    border-radius: 10px !important;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# PATHS
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logo_path = os.path.join(BASE_DIR, "Frontend_logic", "rp2_logo.png")
avatar_path = os.path.join(BASE_DIR, "Frontend_logic", "ai_avatar.png")
history_path = os.path.join(BASE_DIR, "chat_histories")

# =========================================================
# SESSION STATE
# =========================================================
defaults = {
    "page": "config",
    "messages": [],
    "history": "",
    "candidate_name": "",
    "show_feedback": False,
    "last_voice_input": "",
    "latest_audio": None,
    "mic_key": 0
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# VOICE FUNCTION
# =========================================================
def autoplay_audio(text):
    try:
        print("=== TTS START ===")
        
        tts_resp = requests.post(
            f"{BACKEND_URL}/voice/tts",
            json={"text": text},
            timeout=15
        )
        
        print("TTS STATUS:", tts_resp.status_code)
        print("TTS DATA:", tts_resp.text)
        
        data = tts_resp.json()
        audio_url = data.get("audio_url")
        print("AUDIO URL:", audio_url)

        audio_resp = requests.get(
            f"{BACKEND_URL}{data['audio_url']}",
            timeout=15
        )
        print("AUDIO FILE STATUS:", audio_resp.status_code)

        # Step 3: Store base64 in session state for next render
        audio_b64 = base64.b64encode(audio_resp.content).decode()
        st.session_state.pending_audio = audio_b64

    except Exception as e:
        print("AUDIO ERROR:", e)
        st.error(str(e))

# =========================================================
# SAVE HISTORY
# =========================================================
def save_chat_history():
    os.makedirs(history_path, exist_ok=True)
    filename = f"{st.session_state.candidate_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(history_path, filename)
    with open(filepath, "w") as f:
        json.dump({
            "candidate": st.session_state.candidate_name,
            "history": st.session_state.history
        }, f, indent=4)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, width=220)
    if os.path.exists(avatar_path):
        st.image(avatar_path, width=220)
    st.markdown("---")
    if st.button("Admin Dashboard 🔐"):
        st.session_state.page = "admin"
        st.rerun()

# =========================================================
# CONFIG PAGE
# =========================================================
if st.session_state.page == "config":
    st.title("Setup Training")
    st.session_state.candidate_name = st.text_input("Candidate Name:")
    st.session_state.p = st.selectbox("Select Persona:", list(PERSONAS.keys()))
    st.session_state.c = st.selectbox("Choose Training Course:", COURSES)

    if st.button("Start Training Session 🚀"):
        if not st.session_state.candidate_name.strip():
            st.warning("Please enter candidate name")
        else:
            st.session_state.page = "chat"
            st.rerun()

# =========================================================
# CHAT PAGE
# =========================================================
if st.session_state.get("pending_audio"):
    st.markdown(f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{st.session_state.pending_audio}" type="audio/mp3">
        </audio>
    """, unsafe_allow_html=True)
    st.session_state.pending_audio = None

elif st.session_state.page == "chat":
    st.title(f"Training: {st.session_state.p} | Course: {st.session_state.c}")
    st.markdown("---")

    # SHOW CHAT HISTORY
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    st.markdown("---")

    # INPUTS
    prompt = st.text_input("Type your pitch:", key="text_input")

    audio_text = speech_to_text(
        start_prompt="🎙️ Speak",
        stop_prompt="⏹️ Stop",
        language="en",
        use_container_width=True,
        just_once=True,
        key=f"mic_{st.session_state.mic_key}"
    )

    col1, col2 = st.columns(2)
    with col1:
        send_btn = st.button("Send Message 📩")
    with col2:
        end_btn = st.button("End Session & Get Feedback")

    # END SESSION
    if end_btn:
        save_chat_history()
        st.session_state.show_feedback = True
        st.rerun()

    # DETECT INPUT
    user_input = None

    if send_btn and prompt:
        user_input = prompt.strip()
    elif audio_text:
        cleaned = audio_text.strip()
        if cleaned and cleaned != st.session_state.last_voice_input:
            st.session_state.last_voice_input = cleaned
            user_input = cleaned

    # MAIN CHAT FLOW
    if user_input:
        # avoid duplicates
        if (
            st.session_state.messages
            and st.session_state.messages[-1]["role"] == "user"
            and st.session_state.messages[-1]["content"] == user_input
        ):
            st.stop()

        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("user"):
            st.write(user_input)

        try:
            response = get_ai_response(
                message    = user_input,
                persona    = PERSONAS[st.session_state.p],
                course     = st.session_state.c,
                session_id = st.session_state.candidate_name
            )
        except Exception as e:
            response = f"AI ERROR: {e}"

        with st.chat_message("assistant"):
            st.write(response)
            autoplay_audio(response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

        st.session_state.history += f"User: {user_input}\nAI: {response}\n"
        st.session_state.mic_key += 1
        st.rerun()

    # FEEDBACK SECTION
    if st.session_state.show_feedback:
        st.markdown("---")
        st.subheader("Final Performance Feedback")
        try:
            feedback = get_final_feedback(st.session_state.history)
            st.success(feedback)
        except Exception as e:
            st.error(f"Feedback Error: {e}")

        if st.button("Restart Training"):
            st.session_state.messages = []
            st.session_state.history = ""
            st.session_state.show_feedback = False
            st.session_state.last_voice_input = ""
            st.session_state.page = "config"
            st.rerun()

# =========================================================
# ADMIN PAGE
# =========================================================
elif st.session_state.page == "admin":
    st.title("Admin Dashboard")
    if os.path.exists(history_path):
        files = os.listdir(history_path)
        if not files:
            st.warning("No chat histories found")
        else:
            selected = st.selectbox("Select Chat History:", files)
            filepath = os.path.join(history_path, selected)
            with open(filepath, "r") as f:
                data = json.load(f)
            st.text_area("Chat History Log:", data["history"], height=400)
    else:
        st.warning("chat_histories folder not found")

    if st.button("Back to Home"):
        st.session_state.page = "config"
        st.rerun()

