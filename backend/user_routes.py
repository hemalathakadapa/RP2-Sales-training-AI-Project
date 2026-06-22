"""
user_routes.py — extra user endpoints
Include this in main.py:
    from user_routes import router as user_router
    app.include_router(user_router, prefix="/users", tags=["Users"])
"""
from fastapi import APIRouter
from pydantic import BaseModel
from database import update_user_branch, get_user_by_id

router = APIRouter()

class BranchUpdate(BaseModel):
    branch: str

@router.put("/{user_id}/branch")
def set_user_branch(user_id: int, data: BranchUpdate):
    """Update the branch for a user — called by the Streamlit
    frontend on every login and from Admin Branch Management Tools."""
    updated = update_user_branch(user_id, data.branch)
    if updated:
        return {"success": True, "user_id": user_id, "branch": data.branch}
    return {"success": False, "message": "User not found"}

@router.get("/{user_id}/details")
def get_user_details(user_id: int):
    """Return full user record including branch."""
    user = get_user_by_id(user_id)
    if not user:
        return {"user": {}}
    # Remove password before sending
    user.pop("password", None)
    return {"user": user}