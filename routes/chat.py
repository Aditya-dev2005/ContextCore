from fastapi import APIRouter, HTTPException, Header
from models.schemas import QuestionRequest, QuestionResponse
from services.vector_store import get_vectorstore, similarity_search
from services.cache_service import CacheService
from config import Config
from langchain_openai import ChatOpenAI
from routes.auth import verify_token
import time
from typing import Optional

router = APIRouter()

llm = ChatOpenAI(
    model=Config.LLM_MODEL,
    temperature=Config.TEMPERATURE,
    api_key=Config.OPENROUTER_API_KEY,
    base_url=Config.OPENROUTER_BASE_URL
)

cache = CacheService()

def get_user_from_token(authorization: Optional[str]) -> str:
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        username = verify_token(token)
        if username:
            return username
    return "__default__"

def build_prompt(context: str, question: str, history: list) -> str:
    history_text = ""
    if history:
        lines = []
        for msg in history[-6:]:
            role = "User" if msg.role == "user" else "Assistant"
            lines.append(f"{role}: {msg.content}")
        history_text = "\n".join(lines)

    if history_text:
        return f"""You are a helpful assistant answering questions about uploaded documents.
Use the conversation history for context on follow-up questions.

Conversation History:
{history_text}

Context from documents:
{context}

Current Question: {question}

Answer the question using the document context. If the answer is not in the context, say: "Answer is not available in the context."

Answer:"""
    else:
        return f"""Answer the question as detailed as possible from the provided context.
If the answer is not in the context, just say: "Answer is not available in the context."

Context:
{context}

Question:
{question}

Answer:"""

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    authorization: Optional[str] = Header(None)
):
    start_time = time.time()
    user = get_user_from_token(authorization)

    try:
        cache_key = f"{user}:{request.question}"
        cached_response = cache.get_cached_response(cache_key)
        if cached_response:
            print(f"⚡ Cache HIT for user={user}")
            latency_ms = (time.time() - start_time) * 1000
            return QuestionResponse(
                answer=cached_response["answer"],
                sources=cached_response.get("sources", []),
                latency_ms=round(latency_ms, 2)
            )

        vectorstore = get_vectorstore(user=user)
        if vectorstore is None:
            raise HTTPException(status_code=400, detail="No documents indexed yet. Please upload PDFs first.")

        docs = similarity_search(request.question, k=4, user=user)

        if not docs:
            answer = "No relevant information found in the uploaded documents."
            sources = []
        else:
            context = "\n\n".join([doc.page_content for doc in docs])
            sources = list(set([doc.metadata.get("source", "unknown") for doc in docs]))
            prompt = build_prompt(context, request.question, request.conversation_history or [])
            response = llm.invoke(prompt)
            answer = response.content

        cache.cache_response(cache_key, {"answer": answer, "sources": sources})
        latency_ms = (time.time() - start_time) * 1000

        return QuestionResponse(answer=answer, sources=sources, latency_ms=round(latency_ms, 2))

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")