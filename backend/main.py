from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from chat_routes import router as chat_router
from feedback_routes import router as feedback_router
from voice_routes import router as voice_router
from database import create_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ Runs when app STARTS
    print("🚀 Starting AI Sales Coach Backend...")
    create_tables()
    yield
    # ✅ Runs when app STOPS
    print("🛑 Shutting down...")

app = FastAPI(
    title="AI Sales Coach Backend",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router,     prefix="/chat",     tags=["Chat"])
app.include_router(feedback_router, prefix="/feedback", tags=["Feedback"])
app.include_router(voice_router,    prefix="/voice",    tags=["Voice"])

@app.get("/")
def home():
    return {"message": "Backend is running successfully"}

@app.post("/reset")
def reset(session_id: str):
    from database import clear_conversation
    clear_conversation(session_id)
    return {"message": "Conversation reset successfully", "session_id": session_id}
