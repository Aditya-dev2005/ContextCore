import json
import os
import uuid
from datetime import datetime
from typing import List, Optional

HISTORY_FILE = "chat_history.json"

def _load_all() -> dict:
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_all(data: dict):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_session(messages: list, pdfs: list) -> str:
    """Save current session — returns session_id"""
    if not messages:
        return ""
    all_data = _load_all()
    session_id = str(uuid.uuid4())[:8]
    # First user message as title
    first_q = next((m["content"] for m in messages if m["role"] == "user"), "Untitled")
    all_data[session_id] = {
        "id": session_id,
        "title": first_q[:60],
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "messages": messages,
        "pdfs": [p["filename"] for p in pdfs]
    }
    _save_all(all_data)
    return session_id

def load_all_sessions() -> List[dict]:
    """Return all sessions sorted by newest first"""
    all_data = _load_all()
    sessions = list(all_data.values())
    sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return sessions

def load_session(session_id: str) -> Optional[dict]:
    """Load a specific session by ID"""
    all_data = _load_all()
    return all_data.get(session_id)

def delete_session(session_id: str):
    """Delete a session"""
    all_data = _load_all()
    if session_id in all_data:
        del all_data[session_id]
        _save_all(all_data)