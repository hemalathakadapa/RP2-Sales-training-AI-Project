import os
from dotenv import load_dotenv

load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = "llama-3.1-8b-instant"   


FORCE_USE_LLM = None   # True = always use LLM
                       # False = never use LLM (fallback only)
                       # None = auto detect from API key

if FORCE_USE_LLM is True:
    USE_LLM = True
elif FORCE_USE_LLM is False:
    USE_LLM = False
else:
    USE_LLM = bool(GROQ_API_KEY)   


VOICE_ENABLED  = True
VOICE_LANGUAGE = "en"       # language for gTTS
VOICE_SPEED    = False      # False = normal speed, True = slow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "sales_training.db")


APP_HOST = "0.0.0.0"
APP_PORT = 8000
DEBUG    = True