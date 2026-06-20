from pydantic import BaseModel
from typing import List, Optional, Dict, Any

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
    cache_type: Optional[str] = None
    cache_similarity: Optional[float] = None

class UploadResponse(BaseModel):
    message: str
    chunks: int
    filename: str

class EvaluateRequest(BaseModel):
    question: str
    k: Optional[int] = 4

class EvaluateMetrics(BaseModel):
    precision_at_k: float
    mrr: float
    hit_rate: float
    answer_relevance: float
    context_precision: float
    overall_score: float
    details: Dict[str, Any]

class EvaluateResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]
    metrics: EvaluateMetrics
    interpretation: Dict[str, str]
    latency_ms: float