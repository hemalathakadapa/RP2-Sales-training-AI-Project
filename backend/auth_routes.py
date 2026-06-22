
from fastapi import APIRouter
from pydantic import BaseModel
from database import (
    get_user, create_user, update_password, update_user_branch,
    get_admin, create_admin, update_admin_password
)

router = APIRouter()

# ── Pydantic models ──

class RegisterRequest(BaseModel):
    name:     str
    email:    str
    password: str
    branch:   str = ""          # Bangalore / Cochin / Calicut

class LoginRequest(BaseModel):
    email:    str
    password: str

class ResetPasswordRequest(BaseModel):
    email:        str
    new_password: str

class AdminRegisterRequest(BaseModel):
    name:       str
    email:      str
    password:   str
    branch:     str = "All"           # "All" for super_admin, branch name for branch_admin
    admin_role: str = "super_admin"   # "branch_admin" or "super_admin"

class AdminLoginRequest(BaseModel):
    email:    str
    password: str

class UpdateBranchRequest(BaseModel):
    branch: str

# ── User routes ──

@router.post("/register")
def register(data: RegisterRequest):
    print(f"REGISTER REQUEST for email: {data.email}, branch: {data.branch}")
    try:
        user_id = create_user(
            name     = data.name,
            email    = data.email,
            password = data.password,
            branch   = data.branch,
        )
        return {"success": True, "user_id": user_id}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/login")
def login(data: LoginRequest):
    user = get_user(data.email, data.password)
    if not user:
        return {"success": False, "message": "Invalid credentials"}
    return {
        "success": True,
        "user_id": user["id"],
        "name":    user["name"],
        "email":   user["email"],
        "branch":  user.get("branch", ""),
    }

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest):
    updated = update_password(data.email, data.new_password)
    if not updated:
        return {"success": False, "message": "Email not found"}
    return {"success": True, "message": "Password updated"}

# ── Admin routes ──

@router.post("/admin/register")
def admin_register(data: AdminRegisterRequest):
    try:
        admin_id = create_admin(
            name       = data.name,
            email      = data.email,
            password   = data.password,
            branch     = data.branch,
            admin_role = data.admin_role,
        )
        return {"success": True, "admin_id": admin_id}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/admin/login")
def admin_login(data: AdminLoginRequest):
    admin = get_admin(data.email, data.password)
    if not admin:
        return {"success": False, "message": "Invalid admin credentials"}
    return {
        "success":    True,
        "admin_id":   admin["id"],
        "name":       admin["name"],
        "email":      admin["email"],
        "admin_role": admin.get("admin_role", "super_admin"),
        "branch":     admin.get("branch", "All"),
    }

@router.post("/admin/reset-password")
def admin_reset_password(data: ResetPasswordRequest):
    updated = update_admin_password(data.email, data.new_password)
    if not updated:
        return {"success": False, "message": "Email not found"}
    return {"success": True, "message": "Password updated"}