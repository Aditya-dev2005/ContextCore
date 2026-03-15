from pydantic import BaseModel
from typing import List, Optional

class Message(BaseModel):
    role: str       # "user" or "assistant"
    content: str

class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    conversation_history: Optional[List[Message]] = []  

class QuestionResponse(BaseModel):
    answer: str
    sources: List[str] = []
    latency_ms: Optional[float] = None

class UploadResponse(BaseModel):
    message: str
    chunks: int
    filename: str