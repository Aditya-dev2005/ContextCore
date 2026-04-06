from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.user_service import create_user, verify_user
from datetime import datetime, timedelta
import jwt
import os
from typing import Optional 
router = APIRouter()

SECRET_KEY = os.getenv("JWT_SECRET", "contextcore-secret-key-2024")
ALGORITHM = "HS256"
EXPIRE_HOURS = 24

class AuthRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    token: str
    username: str
    message: str

def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(hours=EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except:
        return None


@router.post("/auth/signup", response_model=AuthResponse)
async def signup(req: AuthRequest):
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    user = create_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=409, detail="Username already exists")
    token = create_token(req.username)
    return AuthResponse(token=token, username=req.username, message="Account created!")

@router.post("/auth/login", response_model=AuthResponse)
async def login(req: AuthRequest):
    user = verify_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_token(req.username)
    return AuthResponse(token=token, username=req.username, message="Welcome back!")