from fastapi import APIRouter, HTTPException, Header
from models.schemas import EvaluateRequest, EvaluateResponse, EvaluateMetrics
from services.vector_store import get_vectorstore, similarity_search
from services.evaluation_service import RAGASEvaluator
from config import Config
from langchain_openai import ChatOpenAI
from routes.auth import verify_token
from routes.chat import build_prompt
import time
from typing import Optional

router = APIRouter()

llm = ChatOpenAI(
    model=Config.LLM_MODEL,
    temperature=Config.TEMPERATURE,
    api_key=Config.OPENROUTER_API_KEY,
    base_url=Config.OPENROUTER_BASE_URL
)

evaluator = RAGASEvaluator()


def get_user_from_token(authorization: Optional[str]) -> str:
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        username = verify_token(token)
        if username:
            return username
    return "__default__"


def _interpret(metrics: dict) -> dict:
    def grade(score: float) -> str:
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Fair"
        return "Poor"

    return {
        "overall": grade(metrics["overall_score"]),
        "precision_at_k": grade(metrics["precision_at_k"]),
        "answer_relevance": grade(metrics["answer_relevance"]),
        "context_precision": grade(metrics["context_precision"]),
        "summary": (
            f"Retrieved {metrics['details']['relevant_chunks']}/{metrics['details']['total_chunks']} "
            f"relevant chunks. Overall pipeline quality: {grade(metrics['overall_score'])} "
            f"({metrics['overall_score'] * 100:.1f}%)."
        )
    }


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_answer(
    request: EvaluateRequest,
    authorization: Optional[str] = Header(None)
):
    start_time = time.time()
    user = get_user_from_token(authorization)

    vectorstore = get_vectorstore(user=user)
    if vectorstore is None:
        raise HTTPException(status_code=400, detail="No documents indexed yet. Please upload PDFs first.")

    k = request.k or 4
    docs = similarity_search(request.question, k=k, user=user)

    if not docs:
        raise HTTPException(status_code=404, detail="No relevant chunks retrieved for this question.")

    chunks = [doc.page_content for doc in docs]
    sources = list(set([doc.metadata.get("source", "unknown") for doc in docs]))

    context = "\n\n".join(chunks)
    prompt = build_prompt(context, request.question, [])
    answer = llm.invoke(prompt).content

    metrics_dict = evaluator.evaluate(request.question, answer, chunks)
    interpretation = _interpret(metrics_dict)

    latency_ms = (time.time() - start_time) * 1000

    return EvaluateResponse(
        question=request.question,
        answer=answer,
        sources=sources,
        metrics=EvaluateMetrics(**metrics_dict),
        interpretation=interpretation,
        latency_ms=round(latency_ms, 2)
    )