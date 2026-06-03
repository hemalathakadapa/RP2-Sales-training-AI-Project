import requests
import os
import sys

BACKEND_URL = "https://ai-student-simulator-for-training-sales.onrender.com"

abs_path = os.path.dirname(os.path.abspath(__file__))
if abs_path not in sys.path:
    sys.path.insert(0, abs_path)

import streamlit as st
import json
import tempfile
import datetime
import base64
from persona_config import PERSONAS, COURSES
from gtts import gTTS
from streamlit_mic_recorder import speech_to_text
import streamlit.components.v1 as components
import importlib.util, os

_api_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "services", "api_client.py")
_spec = importlib.util.spec_from_file_location("api_client", _api_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

get_ai_response = _mod.get_ai_response
get_evaluation = _mod.get_evaluation
reset_conversation = _mod.reset_conversation
get_all_sessions = _mod.get_all_sessions
get_session_conversation = _mod.get_session_conversation
rename_chat_session = _mod.rename_chat_session

_pc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "persona_config.py")
_spec2 = importlib.util.spec_from_file_location("persona_config", _pc_path)
_mod2 = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(_mod2)

PERSONAS = _mod2.PERSONAS
COURSES = _mod2.COURSES

# =========================================================
# page config
# =========================================================
logo_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "rp2_logo.png"
)
st.set_page_config(
    page_title="RP2 AI Sales Trainer",
    page_icon="logo_path",
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

st.markdown("""
<style>

.main-header{
    display:flex;
    align-items:center;
    gap:20px;
    margin-bottom:20px;
}

.main-title{
    font-size:42px;
    font-weight:800;
    color:white;
}

.info-card{
    background:rgba(255,255,255,0.06);
    padding:30px;
    border-radius:15px;
    border:1px solid rgba(255,255,255,0.1);
}

.login-card{
    background:white;
    padding:30px;
    border-radius:15px;
    color:black;
}

.course-box{
    background:rgba(255,255,255,0.08);
    padding:15px;
    border-radius:12px;
    margin-top:20px;
}

</style>
""", unsafe_allow_html=True)
# SESSION STATE
# =========================================================
defaults = {
    "page": "landing",
    "authenticated": False,
    "user_id": None,
    "user_name": "",
    "email": "",
    "role": "user",
    "messages": [],
    "history": "",
    "session_id": "",
    "candidate_name": "",
    "p": list(PERSONAS.keys())[0] if PERSONAS else "",
    "c": COURSES[0] if COURSES else "",
    "show_feedback": False,
    "last_voice_input": "",
    "pending_voice_input": "",
    "latest_audio": None,
    "mic_key": 0
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# VOICE FUNCTION
# =========================================================
def autoplay_audio_from_url(audio_url: str):
    """Fetch audio from backend and play it"""
    if not audio_url:
        return
    try:
        r = requests.get(f"{BACKEND_URL}{audio_url}")
        if r.status_code == 200:
            audio_bytes = r.content
            st.audio(r.content, format="audio/mp3", autoplay=True)
        else:
            st.error(f"Audio fetch failed: {r.status_code}")
            
    except Exception as e:
        st.warning(f"Audio playback error: {e}")

def autoplay_audio_local(text: str):
    """Fallback: generate audio locally with gTTS"""
    if not text:
        return
    try:
        tts = gTTS(text=text, lang="en")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
        audio_bytes = open(fp.name, "rb").read()
        b64 = base64.b64encode(audio_bytes).decode("utf-8")
        st.markdown(
            f'<audio autoplay style="display:none"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
            unsafe_allow_html=True
        )
    except Exception as e:
        st.warning(f"Local TTS error: {e}")

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
# SECURITY CHECK
# =========================================================

if (
    st.session_state.page not in ["landing", "admin"]
    and not st.session_state.authenticated
):
    st.session_state.page = "landing"
    st.rerun()

# =========================================================
# SIDEBAR
# =========================================================
if (st.session_state.authenticated and st.session_state.page in ["dashboard", "chat"]):
    with st.sidebar:
        if os.path.exists(logo_path):
            st.image(logo_path, width=220)
        st.markdown(
            f"### Welcome\n{st.session_state.user_name}"
        )
    # =========================
    # NEW CHAT BUTTON
    # =========================

        if st.button("New Session"):
            st.session_state.messages = []
            st.session_state.session_id = ""
            st.session_state.page = "dashboard"
            st.rerun()
            
        st.markdown("---")
        
        st.markdown("## Chat History")
        try:
            sessions = get_all_sessions()
            if sessions:
                for s in sessions:
                    col1, col2 = st.columns([4,1])
                    with col1:
                        title = s.get("title", "New Session")
                        if st.button(title, key=f"load_{s['session_id']}"):
                            history = get_session_conversation(s["session_id"])
                            st.session_state.messages = []
                            for turn in history:
                                st.session_state.messages.append({
                                    "role": "user",
                                    "content": turn["salesperson"]
                                })

                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": turn["student"]
                                 })
                            st.session_state.session_id = s["session_id"]
                            st.session_state.page = "chat"
                            st.rerun()

                    with col2:
                        if st.button("⋮", key=f"rename_btn_{s['session_id']}"):
                            st.session_state.rename_target = s["session_id"]
            else:
                st.info("No chats yet.")
        except Exception as e:
            st.error(f"History Error: {e}")

        # RENAME
        if "rename_target" in st.session_state:
            st.markdown("---")
            new_name = st.text_input("Rename Chat", key="rename_input")

            col1, col2 = st.columns(2)
            with col1:
                save = st.button("Save")
            with col2:
                cancel = st.button("Cancel")
                
            if save:
                try:
                    rename_chat_session(st.session_state.rename_target,new_name)
                    del st.session_state.rename_target
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Rename Error: {e}")
            if cancel:
                del st.session_state.rename_target
                st.rerun()
                    
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user_name = ""
            st.session_state.user_id = None
            st.session_state.page = "landing"
            st.rerun()
                        
# ========================================================
# LANDING PAGE
# =========================================================
if st.session_state.page == "landing":

    # ==========================================
    # HEADER
    # ==========================================

    col1, col2 = st.columns([10,2])

    with col1:

        header1, header2 = st.columns([1,8])

        with header1:
            if os.path.exists(logo_path):
                st.image(logo_path, width=90)

        with header2:
            st.markdown(
                """
                <div class="main-title">
                RP2 SALES TRAINING AGENT
                </div>
                """,
                unsafe_allow_html=True
            )

    with col2:
        if st.button("Admin Dashboard"):
            st.session_state.page = "admin"
            st.rerun()

    st.markdown("---")

    # ==========================================
    # BODY
    # ==========================================

    left, right = st.columns([3,2])

    # ==========================================
    # ABOUT PLATFORM
    # ==========================================

    with left:

        st.markdown('<div class="info-card">', unsafe_allow_html=True)

        st.subheader("About The Platform")

        st.write(
            """
            RP2 SALES TRAINING AGENT is an AI-powered training platform
            designed to help sales counsellors practice realistic student
            interactions before engaging with actual prospects.

            The platform simulates student conversations using AI-generated
            personas, allowing candidates to improve communication,
            objection handling, course pitching, confidence, and sales
            performance. Every session is evaluated automatically and
            detailed feedback is provided to support continuous improvement.
            """
        )

        st.markdown("### Courses Offered")

        st.markdown("""
        ✅ Data Science

        ✅ Data Analytics

        ✅ Agentic AI
        """)

        st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================
    # LOGIN BOX
    # ==========================================

    with right:

        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        st.subheader("Login")

        email = st.text_input(
            "Email",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button("Login"):

            st.session_state.authenticated = True
            st.session_state.user_name = email

            st.session_state.page = "dashboard"

            st.rerun()

        st.markdown("---")

        if st.button("Don't Have An Account? Sign Up"):

            st.session_state.page = "signup"

            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# signup page

elif st.session_state.page == "signup":

    st.title("Create Account")

    name = st.text_input("Full Name")

    email = st.text_input("Email")

    password = st.text_input(
        "Password",
        type="password"
    )

    confirm = st.text_input(
        "Confirm Password",
        type="password"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button("Create Account"):

            st.success(
                "Account Created Successfully. Please Login."
            )

            st.session_state.page = "landing"

            st.rerun()

    with col2:

        if st.button("Back To Login"):

            st.session_state.page = "landing"

            st.rerun()
# =========================================================
#  DASHNOARD
# =========================================================

elif st.session_state.page == "dashboard":

    st.title(f"Welcome {st.session_state.user_name}")
    col1,col2,col3 = st.columns(3)

    col1.metric("Sessions", "15")
    col2.metric("Average Score", "84%")
    col3.metric("Completed Trainings", "9")

    st.markdown("---")

    st.session_state.candidate_name = st.text_input("Candidate Name")
    st.subheader("Select Persona")
    st.session_state.p = st.selectbox(
        "",
        list(PERSONAS.keys())
    )

    st.subheader("Select Course")

    st.session_state.c = st.selectbox(
        "",
        COURSES
    )

    if st.button("Start Training Session"):

        st.session_state.messages = []
        st.session_state.session_id = ""
        st.session_state.show_feedback = False
        st.session_state.page = "chat"

        st.rerun()
# =========================================================
# CHAT PAGE
# =========================================================
elif st.session_state.page == "chat":
    st.title(f"Training: {st.session_state.p} | Course: {st.session_state.c}")
    st.markdown("---")

    # SHOW CHAT HISTORY
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    components.html(
        """
        <script>
            window.parent.document.querySelector('section.main').scrollTo({
                top: window.parent.document.querySelector('section.main').scrollHeight,
                behavior: 'smooth'
            });
        </script>
        """,
        height=0
    )

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
        send_btn = st.button("Send Message")
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
            st.session_state.pending_voice_input = cleaned
            st.session_state.mic_key += 1
            st.rerun()
    if not user_input and st.session_state.get("pending_voice_input"):
        user_input = st.session_state.pending_voice_input
        st.session_state.pending_voice_input = ""

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
            result = get_ai_response(
                message= user_input,
                persona    = st.session_state.p,
                course     = st.session_state.c, 
                session_id   = st.session_state.session_id
            )

            response_text = result.get("response", "Sorry, no response received.")
            audio_url     = result.get("audio_url")

            # ✅ Save session_id returned by backend (set on first message)
            if result.get("session_id"):
                st.session_state.session_id = result["session_id"]

        except Exception as e:
            response_text = f"Backend ERROR: {e}"
            audio_url     = None

        with st.chat_message("assistant"):
            st.write(response_text)
            if audio_url:
                autoplay_audio_from_url(audio_url)
            else:
                autoplay_audio_local(response_text)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text
        })

        if send_btn:
            st.session_state.mic_key += 1

    # FEEDBACK SECTION
    if st.session_state.show_feedback:
        st.markdown("---")
        st.subheader("Final Performance Feedback")
        if not st.session_state.session_id:
            st.warning("No session found — please have a conversation first.")
        else:
            try:
                # ✅ Call backend evaluator
                eval_result = get_evaluation(st.session_state.session_id, mode="full")
                result      = eval_result.get("result", {})
 
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("Final Score",    f"{result.get('final_score', 0)}/10")
                col_b.metric("AI Score",       f"{result.get('groq_score', 0)}/10")
                col_c.metric("Keyword Score",  f"{result.get('keyword_score', 0)}/10")
                col_d.metric("Tone Score",     f"{result.get('tone_score', 0)}/10")
 
                st.markdown("### Skill Breakdown")
                for skill, score in result.get("skill_scores", {}).items():
                    st.progress(int(score * 10), text=f"{skill.replace('_',' ').title()}: {score}/10")
 
                col_l, col_r = st.columns(2)
                with col_l:
                    st.markdown("#### ✅ Strengths")
                    for s in result.get("strengths", []):
                        st.write(f"- {s}")
                with col_r:
                    st.markdown("#### ⚠️ Weaknesses")
                    for w in result.get("weaknesses", []):
                        st.write(f"- {w}")
 
                st.markdown("#### 💡 Suggestions")
                for suggestion in result.get("suggestions", []):
                    st.info(suggestion)

            except Exception as e:
                st.error(f"Feedback Error: {e}")

        if st.button("Restart Training"):
            if st.session_state.session_id:
                try:
                    reset_conversation(st.session_state.session_id)
                except:
                    pass
            st.session_state.messages = []
            st.session_state.session_id = ""
            st.session_state.history = ""
            st.session_state.show_feedback = False
            st.session_state.last_voice_input = ""
            st.session_state.page = "dashboard"
            st.rerun()

# =========================================================
# ADMIN PAGE
# =========================================================
elif st.session_state.page == "admin":
    st.title("Admin Dashboard")
    st.markdown("### Training Analytics")
    try:
        sessions = get_all_sessions()
 
        if not sessions:
            st.warning("No sessions found yet.")
        else:
            # Build display labels
            labels = {
                f"{s['title']} | {s['session_id']} | {s['updated_at']}": s["session_id"]
                for s in sessions
            }
            selected_label = st.selectbox("Select Session:", list(labels.keys()))
            selected_id    = labels[selected_label]
 
            if st.button("Load Conversation"):
                history = get_session_conversation(selected_id)
                if history:
                    for turn in history:
                        st.markdown(f"**🧑 Salesperson:** {turn['salesperson']}")
                        st.markdown(f"**🤖 Student:** {turn['student']}")
                        st.markdown(f"*{turn['timestamp']}*")
                        st.markdown("---")
                else:
                    st.warning("No conversation found for this session.")
 
            if st.button("Evaluate This Session"):
                try:
                    eval_result = get_evaluation(selected_id, mode="full")
                    st.json(eval_result.get("result", {}))
                except Exception as e:
                    st.error(f"Evaluation error: {e}")
 
    except Exception as e:
        st.error(f"Could not load sessions: {e}")

    if st.button("Back to Home"):
        st.session_state.page = "dashboard"
        st.rerun()
        
st.markdown("---")
