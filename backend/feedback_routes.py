from fastapi import APIRouter
import asyncio

router = APIRouter()

@router.get("/sessions")
def get_sessions():
    """Get all past sessions for session picker"""
    try:
        from database import get_all_sessions
        sessions = get_all_sessions()
        return {"sessions": sessions}
    except Exception as e:
        print("Sessions Error:", e)
        return {"error": "Could not fetch sessions"}

@router.get("/evaluate/{session_id}")       # ✅ session_id in URL
async def evaluate(session_id: str, mode: str = "recent"):
    
    try:
        from database import get_conversation, save_feedback
        from evaluator import evaluate_conversation

        # ✅ Get limit based on mode
        if mode in ("full", "summary"):
            limit = 999        # all turns
        else:
            limit = 10         # last 10 only

        # ✅ Get THIS student's history
        history = get_conversation(
            session_id = session_id,
            limit      = limit
        )

        if not history:
            return {"error": "No conversation found for this session"}

        # ✅ Evaluate — result is already a dict
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, evaluate_conversation, history, mode
            ),
            timeout=25.0  # Render free tier limit is ~30s
        )

        # ✅ Save feedback to database
        save_feedback(
            session_id = session_id,
            score      = result.get("final_score", 0),
            groq_score  = result.get("groq_score",  0),
            keyword_score = result.get("keyword_score", 0),
            tone_score    = result.get("tone_score",    0),
            summary    = str(result)
        )

        return {
            "session_id": session_id,
            "mode":       mode,
            "result":     result
        }
    except asyncio.TimeoutError:
        print("Evaluate Timeout: LLM took too long")
        return {
            "error": "Evaluation timed out. Try mode=recent instead of mode=full"
        }

    except Exception as e:
        print("Evaluate Error:", e)
        return {"error": "Something went wrong during evaluation"}


@router.get("/history/{session_id}")        # ✅ session_id in URL
def feedback_history(session_id: str):
    """
    Get all past evaluations for one student

    Usage:
    GET /feedback/history/abc-123
    """
    try:
        from database import get_feedback_history

        history = get_feedback_history(session_id)

        if not history:
            return {"error": "No feedback history found"}

        return {
            "session_id": session_id,
            "history":    history
        }

    except Exception as e:
        print("History Error:", e)
        return {"error": "Something went wrong fetching history"}
