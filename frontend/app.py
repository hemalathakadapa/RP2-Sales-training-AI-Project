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
from gtts import gTTS
import pandas as pd
from streamlit_mic_recorder import speech_to_text
import importlib.util, os

_api_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "services", "api_client.py")
_spec = importlib.util.spec_from_file_location("api_client", _api_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

get_ai_response = _mod.get_ai_response
register_user = _mod.register_user
login_user = _mod.login_user
get_evaluation = _mod.get_evaluation
reset_conversation = _mod.reset_conversation
get_all_sessions = _mod.get_all_sessions
get_session_conversation = _mod.get_session_conversation
rename_chat_session = _mod.rename_chat_session
get_user_sessions = _mod.get_user_sessions
get_all_users = _mod.get_all_users
get_user_dashboard = _mod.get_user_dashboard
get_course_metrics = _mod.get_course_metrics
reset_password = _mod.reset_password 

_pc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "persona_config.py")
_spec2 = importlib.util.spec_from_file_location("persona_config", _pc_path)
_mod2 = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(_mod2)

PERSONAS = _mod2.PERSONAS
COURSES = _mod2.COURSES

# =========================================================
# page config
# =========================================================
logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rp2_logo.png")
history_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history")

st.set_page_config(
    page_title="RP2 AI Sales Trainer",
    page_icon=logo_path,
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>

/* ── HIDE STREAMLIT TOP TOOLBAR & HEADER ── */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* BACKGROUND */
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364) !important;
}

/* MAIN CONTAINER */
.block-container {
    padding: 2rem 3rem !important;
    background: transparent !important;
}

/* ── FORCE SIDEBAR ALWAYS OPEN ── */
section[data-testid="stSidebar"] {
    background-color: #0b1220 !important;
    min-width: 300px !important;
    width: 300px !important;
    transform: translateX(0) !important;
    visibility: visible !important;
    display: block !important;
    margin-left: 0 !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 300px !important;
    width: 300px !important;
    transform: translateX(0) !important;
    margin-left: 0 !important;
    display: block !important;
    visibility: visible !important;
}
section[data-testid="stSidebar"] * {
    color: white !important;
}

/* ── HIDE SIDEBAR TOGGLE BUTTONS ── */
[data-testid="collapsedControl"] { display: none !important; }
button[aria-label="Close sidebar"] { display: none !important; }
button[aria-label="Open sidebar"] { display: none !important; }

/* ── SIDEBAR BUTTONS ── */
section[data-testid="stSidebar"] .stButton button[data-testid="baseButton-secondary"],
section[data-testid="stSidebar"] .stButton button[data-testid="baseButton-secondaryFormSubmit"],
section[data-testid="stSidebar"] .stButton button {
    background-color: #0b1220 !important;
    background-image: none !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    box-shadow: none !important;
    transform: none !important;
    font-weight: 400 !important;
    font-size: 13px !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: rgba(255,255,255,0.08) !important;
    background-image: none !important;
    border-color: rgba(255,255,255,0.35) !important;
    box-shadow: none !important;
    transform: none !important;
}
section[data-testid="stSidebar"] .stButton > button:focus,
section[data-testid="stSidebar"] .stButton > button:active {
    background-color: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
    transform: none !important;
}

/* ── SIDEBAR ⋮ POPOVER BUTTON ── */
section[data-testid="stSidebar"] [data-testid="stPopover"] button {
    background: transparent !important;
    background-image: none !important;
    color: white !important;
    border: none !important;
    padding: 0.2rem 0.3rem !important;
    font-size: 16px !important;
    box-shadow: none !important;
}

/* ── GLOBAL TEXT ── */
.stApp h1, .stApp h2, .stApp h3,
.stApp h4, .stApp h5, .stApp h6 { color: white !important; }
.stApp p, .stApp li { color: rgba(255,255,255,0.9) !important; }

/* ── WIDGET LABELS ── */
.stApp .stTextInput > label,
.stApp .stSelectbox > label,
.stApp .stRadio > label {
    color: white !important;
    font-weight: 600 !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stTextInput > div > div > input:focus {
    background-color: #ffffff !important;
    color: #111111 !important;
    border-radius: 10px !important;
    border: 1.5px solid #4facfe !important;
}

/* ── MAIN PAGE BUTTONS (gradient) ── */
.stApp > div:not(section[data-testid="stSidebar"]) .stButton > button {
    background: linear-gradient(90deg, #4facfe, #00f2fe) !important;
    color: #000000 !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    width: 100% !important;
    padding: 0.5rem 1rem !important;
    font-size: 15px !important;
}
.stApp > div:not(section[data-testid="stSidebar"]) .stButton > button:hover {
    opacity: 0.9 !important;
    transform: scale(1.01) !important;
}

/* ── CHAT MESSAGES ── */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.10) !important;
    border-radius: 12px !important;
    padding: 10px !important;
}

/* ── DIVIDER ── */
hr { border-color: rgba(255,255,255,0.15) !important; }

/* ── INFO CARD ── */
.info-card {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    border-radius: 16px !important;
    padding: 2rem !important;
    height: 100% !important;
}
.info-card h3, .info-card p, .info-card li { color: white !important; }

/* ── LOGIN CARD ── */
div[data-testid="column"]:nth-of-type(2) > div:first-child {
    background: white !important;
    border-radius: 16px !important;
    padding: 2rem !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
}
div[data-testid="column"]:nth-of-type(2) label,
div[data-testid="column"]:nth-of-type(2) p,
div[data-testid="column"]:nth-of-type(2) h2,
div[data-testid="column"]:nth-of-type(2) h3 { color: #111111 !important; }

/* ── COURSE BADGES ── */
.course-badge {
    display: inline-block;
    background: rgba(79,172,254,0.15);
    border: 1.5px solid #4facfe;
    color: #4facfe;
    padding: 5px 16px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 600;
    margin: 5px 5px 5px 0;
}

/* ── MAIN TITLE ── */
.main-title {
    font-size: 38px;
    font-weight: 800;
    color: white !important;
    line-height: 1.15;
    margin: 0;
    padding: 0;
}

/* ── METRIC CARDS ── */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}
[data-testid="stMetric"] label,
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] { color: white !important; }

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
    "qualification": "12th Pass",
    "subject": "Science",
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
            b64 = base64.b64encode(r.content).decode("utf-8")
            st.markdown(
                f'<audio autoplay style="display:none"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
                unsafe_allow_html=True
            )    
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

# =================================================
# RESET PASSWORD
# =================================================

def reset_password(email, new_password):
    response = requests.post(
        f"{BACKEND_URL}/auth/reset-password",
        json={"email": email, "new_password": new_password}
    )
    return response.json()

# =================================================
# ADMIN PASSWORD FUNCTION
# =================================================

def admin_login_user(email, password):
    response = requests.post(
        f"{BACKEND_URL}/auth/admin/login",
        json={"email": email, "password": password}
    )
    return response.json()

def admin_register_user(name, email, password):
    response = requests.post(
        f"{BACKEND_URL}/auth/admin/register",
        json={"name": name, "email": email, "password": password}
    )
    return response.json()

def admin_reset_password(email, new_password):
    response = requests.post(
        f"{BACKEND_URL}/auth/admin/reset-password",
        json={"email": email, "new_password": new_password}
    )
    return response.json()

# =================================================
# SECURITY CHECK
# =================================================
PROTECTED_PAGES = {"dashboard", "chat", "admin"}
 
if st.session_state.page in PROTECTED_PAGES and not st.session_state.authenticated:
    st.session_state.page = "landing"
    st.rerun()

# =========================================================
# SIDEBAR
# =========================================================
if (st.session_state.authenticated and st.session_state.page in ["dashboard", "chat"]):
    with st.sidebar:
        if os.path.exists(logo_path):
            st.image(logo_path, width=220)
        st.markdown(f"### Welcome\n{st.session_state.user_name}")

        # NEW SESSION BUTTON
        if st.button("New Session", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = ""
            st.session_state.page = "dashboard"
            st.rerun()
 
        st.markdown("---")
        st.markdown("## Chat History")
 
        try:
            sessions = get_user_sessions(st.session_state.user_id)
            if sessions:
                for s in sessions:
                    title = s.get("title", "New Session")
                    display_title = title if len(title) <= 28 else title[:28] + "..."
                    
                    c1, c2 = st.columns([10, 1], gap="small")
                    with c1:
                        if st.button(display_title, key=f"load_{s['session_id']}", use_container_width=True, help=title):
                            history = get_session_conversation(s["session_id"], st.session_state.user_id)
                            st.session_state.messages = []
                            for turn in history:
                                st.session_state.messages.append({"role": "user", "content": turn["salesperson"]})
                                st.session_state.messages.append({"role": "assistant", "content": turn["student"]})
                            st.session_state.session_id = s["session_id"]
                            st.session_state.page = "chat"
                            st.rerun()
                    with c2:
                        with st.popover("⋮", use_container_width=True):
                            new_name = st.text_input(
                                "New name",
                                value=title,
                                key=f"rename_input_{s['session_id']}"
                            )
                            if st.button("Save", key=f"save_{s['session_id']}", use_container_width=True):
                                try:
                                    rename_chat_session(s["session_id"], new_name)
                                    st.session_state[f"popover_open_{s['session_id']}"] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Rename Error: {e}")
                            if st.button("Cancel", key=f"cancel_{s['session_id']}", use_container_width=True):
                                st.rerun()           
            else:
                st.info("No chats yet.")
        except Exception as e:
            st.error(f"History Error: {e}")
 
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back to Home", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_name = ""
                st.session_state.user_id = None
                st.session_state.page = "landing"
                st.rerun()
        with col2:
            if st.button("Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_name = ""
                st.session_state.user_id = None
                st.session_state.page = "landing"
                st.rerun()
        
# ========================================================
# LANDING PAGE
# =========================================================
if st.session_state.page == "landing":

    col1, col2 = st.columns([10,2])
    with col1:
        h1, h2 = st.columns([1,8])
        with h1:
            if os.path.exists(logo_path):
                st.image(logo_path, width=150)
        with h2:
            st.markdown(
                """
                <div class="main-title">
                RP2 SALES TRAINING AGENT
                </div>
                """,
                unsafe_allow_html=True
            )
    with col2:
        if st.button("Admin", key="btn_admin_landing"):
            st.session_state.page = "admin_login"
            st.rerun()

    st.markdown ("---")
 
    left, right = st.columns([3, 2], gap="large")
 
    with left:
        st.markdown("""
        <div class="info-card">
            <h3 style="color:white;margin-top:0">About The Platform</h3>
            <p style="color:rgba(255,255,255,0.88);line-height:1.7">
                RP2 SALES TRAINING AGENT is an AI-powered training platform
                designed to help sales counsellors practice realistic student
                interactions before engaging with actual prospects.
            </p>
            <p style="color:rgba(255,255,255,0.88);line-height:1.7">
                The platform simulates student conversations using AI-generated
                personas, allowing candidates to improve communication,
                objection handling, course pitching, confidence, and sales
                performance. Every session is evaluated automatically and
                detailed feedback is provided to support continuous improvement.
            </p>
            <h4 style="color:white;margin-bottom:10px">Courses Offered</h4>
            <span class="course-badge">✦ Data Science</span>
            <span class="course-badge">✦ Data Analytics</span>
            <span class="course-badge">✦ Agentic AI</span>
        </div>
        """, unsafe_allow_html=True)
 
    with right:
        st.markdown("<h3 style='color:#111;margin-bottom:0.5rem'>User Login</h3>", unsafe_allow_html=True)
 
        email    = st.text_input("Email",    key="login_email",    placeholder="you@example.com",  label_visibility="visible")
        password = st.text_input("Password", key="login_password", type="password",                label_visibility="visible")
 
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
 
        if st.button("Login", key="btn_login"):
            if not email.strip():
                st.error("Please enter your email.")
            elif "@" not in email:
                st.error("Please enter a valid email address.")
            elif not password:
                st.error("Please enter your password.")
            else:
                result = login_user(email=email, password=password)
                if result.get("success"):
                    st.session_state.authenticated = True
                    st.session_state.user_name = result["name"]
                    st.session_state.user_id = result.get("user_id")
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error(result["message"])
 
        st.markdown("<hr style='border-color:#ddd;margin:1rem 0'>", unsafe_allow_html=True)

        if st.button("Forgot Password?"):
            st.session_state.page = "forgot_password"
            st.rerun()
 
        if st.button("Don't Have An Account? Sign Up", key="btn_goto_signup"):
            st.session_state.page = "signup"
            st.rerun()

# FORGOT PASSWORD
elif st.session_state.page == "forgot_password":

    st.title("Reset Password")

    email = st.text_input("Registered Email")
    new_password = st.text_input(
        "New Password",
        type="password"
    )

    confirm_password = st.text_input(
        "Confirm Password",
        type="password"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Reset Password"):
            if not email.strip():
                st.error("Please enter your email.")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                result = reset_password(email, new_password)

                if result.get("success"):
                    st.success("Password updated successfully")
                    st.session_state.page = "landing"
                    st.rerun()
                else:
                    st.error(result.get("message"))

    with col2:
        if st.button("Back"):
            st.session_state.page = "landing"
            st.rerun()

# =========================================================
# ADMIN LOGIN PAGE
# =========================================================
elif st.session_state.page == "admin_login":

    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("<h2 style='text-align:center'>Admin Login</h2>", unsafe_allow_html=True)

        email    = st.text_input("Email",    key="admin_login_email",    placeholder="admin@example.com")
        password = st.text_input("Password", key="admin_login_password", type="password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login", key="btn_admin_login"):
                if not email.strip():
                    st.error("Please enter your email.")
                elif "@" not in email:
                    st.error("Invalid email address.")
                elif not password:
                    st.error("Please enter your password.")
                else:
                    result = admin_login_user(email=email, password=password)
                    if result.get("success"):
                        st.session_state.authenticated = True
                        st.session_state.role          = "admin"
                        st.session_state.user_name     = result["name"]
                        st.session_state.user_id       = result.get("admin_id")
                        st.session_state.page          = "admin"
                        st.rerun()
                    else:
                        st.error(result.get("message", "Login failed. Please try again."))
        with col2:
            if st.button("Back", key="btn_admin_login_back"):
                st.session_state.page = "landing"
                st.rerun()

        st.markdown("<hr style='border-color:#ddd;margin:1rem 0'>", unsafe_allow_html=True)

        if st.button("Forgot Password?", key="btn_admin_forgot"):
            st.session_state.page = "admin_forgot_password"
            st.rerun()

        if st.button("Don't Have An Account? Sign Up", key="btn_goto_admin_signup"):
            st.session_state.page = "admin_signup"
            st.rerun()


# =========================================================
# ADMIN SIGNUP PAGE
# =========================================================
elif st.session_state.page == "admin_signup":

    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("<h2 style='text-align:center'>Create Admin Account</h2>", unsafe_allow_html=True)

        if st.session_state.get("admin_signup_done"):
            st.success("Admin account created successfully.")
            if st.button("Back to Admin Login", key="btn_admin_signup_done_back"):
                st.session_state.admin_signup_done = False
                st.session_state.page = "admin_login"
                st.rerun()
        else:
            name     = st.text_input("Full Name",       key="admin_signup_name",     placeholder="John Smith")
            email    = st.text_input("Email",            key="admin_signup_email",    placeholder="admin@example.com")
            password = st.text_input("Password",         key="admin_signup_password", type="password")
            confirm  = st.text_input("Confirm Password", key="admin_signup_confirm",  type="password")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Create Account", key="btn_admin_create"):
                    if not name.strip():
                        st.error("Full name is required.")
                    elif not email.strip():
                        st.error("Email is required.")
                    elif "@" not in email:
                        st.error("Invalid email address.")
                    elif not password:
                        st.error("Password is required.")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        result = admin_register_user(name=name, email=email, password=password)
                        if result.get("success"):
                            st.success("Admin account created successfully.")
                            st.session_state.page = "admin_login"
                            st.rerun()
                        else:
                            st.error(result.get("message", "Registration failed. Please try again."))
            with col2:
                if st.button("Back to Admin Login", key="btn_admin_signup_back"):
                    st.session_state.page = "admin_login"
                    st.rerun()

# =========================================================
# SIGNUP PAGE
# =========================================================
elif st.session_state.page == "signup":
 
    # Centered layout
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("<h2 style='color:white;text-align:center'>Create Account</h2>", unsafe_allow_html=True)

        if st.session_state.get("signup_done"):
            st.success("Account created successfully")
            if st.button("Back to Login", key="btn_signup_done_back"):
                st.session_state.signup_done = False
                st.session_state.page = "landing"
                st.rerun()
        else:
            name     = st.text_input("Full Name",         key="signup_name",     placeholder="John Smith")
            email    = st.text_input("Email",              key="signup_email",    placeholder="you@example.com")
            password = st.text_input("Password",           key="signup_password", type="password")
            confirm  = st.text_input("Confirm Password",   key="signup_confirm",  type="password")
 
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Create Account", key="btn_create"):
                    if not name.strip():
                        st.error("Full name is required.")
                    elif not email.strip():
                        st.error("Email is required.")
                    elif "@" not in email:
                        st.error("Please enter a valid email address.")
                    elif not password:
                        st.error("Password is required.")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        result = register_user( name=name, email=email, password=password)
                        if result.get("success"):
                            st.session_state.signup_done = True
                            st.rerun()
                        else:
                            st.error(result.get("message", "Registration failed. Please try again."))
                            
            with col2:
                if st.button("Back to Home", key="btn_back"):
                    st.session_state.page = "landing"
                    st.rerun()         
 
        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# ADMIN FORGOT PASSWORD PAGE
# =========================================================
elif st.session_state.page == "admin_forgot_password":

    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("<h2 style='text-align:center'>Reset Admin Password</h2>", unsafe_allow_html=True)

        email            = st.text_input("Registered Email",    key="admin_forgot_email")
        new_password     = st.text_input("New Password",        key="admin_forgot_new",     type="password")
        confirm_password = st.text_input("Confirm Password",    key="admin_forgot_confirm", type="password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Reset Password", key="btn_admin_reset"):
                if not email.strip():
                    st.error("Please enter your email.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    result = admin_reset_password(email, new_password)
                    if result.get("success"):
                        st.success("Password updated successfully.")
                        st.session_state.page = "admin_login"
                        st.rerun()
                    else:
                        st.error(result.get("message", "Reset failed. Please try again."))
        with col2:
            if st.button("Back to Admin Login", key="btn_admin_forgot_back"):
                st.session_state.page = "admin_login"
                st.rerun()

# =========================================================
#  DASHBOARD
# =========================================================

elif st.session_state.page == "dashboard":

    st.title(f"Welcome {st.session_state.user_name}")
    user_id = st.session_state.user_id
    dashboard = get_user_dashboard(user_id)

    col1, col2 = st.columns(2)
    col1.metric("Average Score", f"{dashboard['average_score']}%")
    col2.metric("Sessions Completed", dashboard["sessions_completed"])

    st.markdown("---")
    
    st.subheader("Course Performance")

    course_metrics = get_course_metrics(user_id)

    if course_metrics:

        cards_html = """
        <div style="display:flex; gap:20px; flex-wrap:wrap;">
        """

        for item in course_metrics:

            cards_html += f"""
            <div style="
                border:2px solid #D1D5DB;
                border-radius:12px;
                padding:20px;
                min-width:220px;
                background:rgba(255,255,255,0.03);
            ">
                <h3>{item['course']}</h3>

                <div style="color:#E5E7EB; font-size:14px;">
                    Sessions: <b style="color:#FFFFFF;">{item['sessions']}</b>
                </div>

                <div style="color:#E5E7EB; font-size:14px; margin-top:8px;">
                    Avg Score: <b style="color:#FFFFFF;">{item['average_score']}%</b>
                </div>
            </div>
            """

        cards_html += "</div>"

        st.html(cards_html)
        
    qualification_options = [
        "12th Pass",
        "Diploma",
        "ITI",
        "Undergraduate (Pursuing)",
        "Undergraduate (Completed)",
        "Postgraduate (Pursuing)",
        "Postgraduate (Completed)",
        "Working Professional",
        "Career Break / Job Seeker"
    ]

    subject_options = [
        "Science",
        "Commerce",
        "Arts & Humanities",
        "Computer Science / IT",
        "Engineering",
        "Electronics & Communication",
        "Mechanical Engineering",
        "Civil Engineering",
        "Electrical Engineering",
        "Data Science & AI",
        "Mathematics & Statistics",
        "Business Administration",
        "Finance & Accounting",
        "Marketing",
        "Healthcare & Nursing",
        "Pharmacy",
        "Life Sciences / Biotechnology",
        "Education & Teaching",
        "Law",
        "Media & Communication",
        "Hospitality & Tourism",
        "Design & Architecture",
        "Other"
    ]

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.qualification = st.selectbox("Highest Qualification", qualification_options)
    with col2:
        st.session_state.subject = st.selectbox("Academic Background", subject_options)

    st.markdown("### Training Configuration")

    col3, col4 = st.columns(2)
    with col3:
        st.session_state.p = st.selectbox("Student Persona", list(PERSONAS.keys()))
    with col4:
        st.session_state.c = st.selectbox("Course to Pitch", COURSES)

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
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"🎓 Qualification\n\n{st.session_state.qualification}")
    with col2:
        st.info(f"📚 Academic Background\n\n{st.session_state.subject}")

    st.markdown("---")

    # SHOW CHAT HISTORY
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    st.html(
        """
        <script>
            window.parent.document.querySelector('section.main').scrollTo({
                top: window.parent.document.querySelector('section.main').scrollHeight,
                behavior: 'smooth'
            });
        </script>
        """
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
                qualification=st.session_state.qualification,
                subject      =st.session_state.subject,
                session_id   = st.session_state.session_id,
                user_id    = st.session_state.user_id 
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

# =========================================================
# ADMIN PAGE
# =========================================================
elif st.session_state.page == "admin":

    if st.session_state.get("role") != "admin":
        st.error("Access denied. Admins only.")
        if st.button("Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        st.stop()

    # Top bar: title + buttons right-aligned
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        st.title("Admin Dashboard")
    with top_col2:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Back to Home", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.role = None
                st.session_state.user_id = None
                st.session_state.user_name = ""
                if "admin_history" in st.session_state:
                    del st.session_state.admin_history
                st.session_state.page = "landing"
                st.rerun()
        with btn_col2:
            if st.button("Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.role = None
                st.session_state.user_id = None
                st.session_state.user_name = ""
                if "admin_history" in st.session_state:
                    del st.session_state.admin_history
                st.session_state.page = "landing"
                st.rerun()

    st.markdown("### Training Analytics")

    try:
        users = get_all_users()

        if not users:
            st.warning("No users found.")
        else:
            user_options = {
                f"{u['name']} ({u['email']})": u["id"]
                for u in users
            }
            selected_user_label = st.selectbox("Select User", list(user_options.keys()))
            selected_user_id = user_options[selected_user_label]
            sessions = get_user_sessions(selected_user_id)

            dashboard = get_user_dashboard(selected_user_id)
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Average Score", f"{dashboard['average_score']}%")
            with col_b:
                st.metric("Sessions Completed", dashboard["sessions_completed"])

            st.markdown("### Course Performance")
            course_metrics = get_course_metrics(selected_user_id)
            if course_metrics:
                cols = st.columns(min(len(course_metrics), 4))
                for i, item in enumerate(course_metrics):
                    with cols[i % len(cols)]:
                        st.html(f"""
                            <div style="
                                border:1px solid #444;
                                border-radius:10px;
                                padding:15px;
                                margin-bottom:10px;
                                background-color:rgba(255,255,255,0.03);
                            ">
                                <h4 style="color:white;">{item['course']}</h4>
                                <p style="color:white;"><b>Sessions:</b> {item['sessions']}</p>
                                <p style="color:white;"><b>Avg Score:</b> {item['average_score']}%</p>
                            </div>
                        """)

            df = pd.DataFrame(dashboard["performance"])
            if not df.empty:
                st.subheader("Performance Growth")
                st.caption("Running average performance across all completed sessions.")
                chart_df = df.rename(columns={"session_id": "Session", "growth_score": "Growth Score"})
                st.line_chart(chart_df.set_index("Session"))

            # ── Session filters ── (all inside the users else block)
            if not sessions:
                st.warning("No sessions for this user.")
            else:
                col_p, col_c = st.columns(2)
                with col_p:
                    personas = sorted(set(s.get("persona", "N/A") for s in sessions))
                    selected_persona = st.selectbox("Filter by Persona", ["All"] + personas)
                with col_c:
                    courses = sorted(set(s.get("course", "N/A") for s in sessions))
                    selected_course = st.selectbox("Filter by Course", ["All"] + courses)

                filtered_sessions = sessions
                if selected_persona != "All":
                    filtered_sessions = [s for s in filtered_sessions if s.get("persona", "N/A") == selected_persona]
                if selected_course != "All":
                    filtered_sessions = [s for s in filtered_sessions if s.get("course", "N/A") == selected_course]

                if not filtered_sessions:
                    st.warning("No sessions available for this filter, try another.")
                else:
                    session_options = {
                        f"{s['title']} | {s.get('persona','N/A')} | {s.get('course','N/A')} | {s['updated_at']}":
                        s["session_id"]
                        for s in filtered_sessions
                    }

                    selected_session_label = st.selectbox("Select Session", list(session_options.keys()))
                    selected_session_id = session_options[selected_session_label]

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Load Conversation"):
                            history = get_session_conversation(selected_session_id, selected_user_id)
                            if history:
                                st.subheader("Conversation History")
                                for turn in history:
                                    with st.chat_message("user"):
                                        st.write(turn["salesperson"])
                                    with st.chat_message("assistant"):
                                        st.write(turn["student"])
                                    st.caption(turn["timestamp"])
                            else:
                                st.warning("No conversation found.")

                    with col2:
                        if st.button("Evaluate This Session"):
                            eval_result = get_evaluation(selected_session_id, mode="full")
                            result = eval_result.get("result", {})
                            st.subheader("Evaluation Result")

                            ecol1, ecol2, ecol3 = st.columns(3)
                            with ecol1:
                                st.metric("Final Score",   f"{result.get('final_score', 0)}%")
                            with ecol2:
                                st.metric("Keyword Score", f"{result.get('keyword_score', 0)}%")
                            with ecol3:
                                st.metric("Tone Score",    f"{result.get('tone_score', 0)}%")

                            skills = result.get("skill_scores", {})
                            if skills:
                                st.subheader("Skill Breakdown")
                                skill_df = pd.DataFrame({"Skill": list(skills.keys()), "Score": list(skills.values())})
                                st.bar_chart(skill_df.set_index("Skill"))

                            strengths = result.get("strengths", [])
                            if strengths:
                                st.subheader("Strengths")
                                for item in strengths:
                                    st.success(item)

                            weaknesses = result.get("weaknesses", [])
                            if weaknesses:
                                st.subheader("Areas for Improvement")
                                for item in weaknesses:
                                    st.warning(item)

                            suggestions = result.get("suggestions", [])
                            if suggestions:
                                st.subheader("Suggestions")
                                for item in suggestions:
                                    st.info(item)

    except Exception as e:
        st.error(f"Could not load admin dashboard: {e}")

