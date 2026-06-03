from fastapi import APIRouter
from pydantic import BaseModel
from database import get_user, create_user

router = APIRouter()

users = {}

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(data: dict):

    try:
        create_user(
            data["name"],
            data["email"],
            data["password"]
        )

        return {
            "success": True
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@router.post("/login")
def login(data: dict):

    user = get_user(
        data["email"],
        data["password"]
    )

    if not user:
        return {
            "success": False,
            "message": "Invalid credentials"
        }

    return {
        "success": True,
        "name": user["name"],
        "email": user["email"]
    }
