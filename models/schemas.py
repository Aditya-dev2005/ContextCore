from pydantic import BaseModel
from typing import List, Optional

class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class QuestionResponse(BaseModel):
    answer: str
    sources: List[str] = []
    latency_ms: Optional[float] = None

class UploadResponse(BaseModel):
    message: str
    chunks: int
    filename: str