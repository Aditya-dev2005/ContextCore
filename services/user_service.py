import json
import os
import hashlib
import uuid
from typing import Optional

USERS_FILE = "users.json"

def _load() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def _save(data: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str) -> Optional[dict]:
    users = _load()
    if username in users:
        return None  # already exists
    users[username] = {
        "id": str(uuid.uuid4())[:8],
        "username": username,
        "password": _hash(password)
    }
    _save(users)
    return users[username]

def verify_user(username: str, password: str) -> Optional[dict]:
    users = _load()
    user = users.get(username)
    if not user:
        return None
    if user["password"] != _hash(password):
        return None
    return user

def get_user(username: str) -> Optional[dict]:
    return _load().get(username)