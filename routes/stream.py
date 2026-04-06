from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from models.schemas import QuestionRequest
from services.vector_store import get_vectorstore, similarity_search
from services.cache_service import CacheService
from config import Config
from langchain_openai import ChatOpenAI
from routes.auth import verify_token
import json
import time
from typing import Optional

router = APIRouter()
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

Conversation History:
{history_text}

Context from documents:
{context}

Current Question: {question}

Answer:"""
    else:
        return f"""Answer the question as detailed as possible from the provided context.
If the answer is not in the context, just say: "Answer is not available in the context."

Context:
{context}

Question:
{question}

Answer:"""

@router.post("/stream")
async def stream_answer(
    request: QuestionRequest,
    authorization: Optional[str] = Header(None)
):
    user = get_user_from_token(authorization)
    cache_key = f"{user}:{request.question}"

    # Cache hit — stream cached answer
    cached = cache.get_cached_response(cache_key)
    if cached:
        print(f"⚡ Cache HIT (stream) user={user}")
        answer = cached["answer"]
        sources = cached.get("sources", [])

        def cached_stream():
            words = answer.split(" ")
            for i, word in enumerate(words):
                chunk = word if i == 0 else " " + word
                yield f"data: {json.dumps({'token': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True, 'sources': sources, 'cached': True})}\n\n"

        return StreamingResponse(cached_stream(), media_type="text/event-stream")

    # Check vectorstore
    vectorstore = get_vectorstore(user=user)
    if vectorstore is None:
        raise HTTPException(status_code=400, detail="No documents indexed yet. Please upload PDFs first.")

    docs = similarity_search(request.question, k=4, user=user)

    if not docs:
        def no_docs_stream():
            yield f"data: {json.dumps({'token': 'No relevant information found in the uploaded documents.'})}\n\n"
            yield f"data: {json.dumps({'done': True, 'sources': []})}\n\n"
        return StreamingResponse(no_docs_stream(), media_type="text/event-stream")

    context = "\n\n".join([doc.page_content for doc in docs])
    sources = list(set([doc.metadata.get("source", "unknown") for doc in docs]))
    prompt = build_prompt(context, request.question, request.conversation_history or [])

    llm_stream = ChatOpenAI(
        model=Config.LLM_MODEL,
        temperature=Config.TEMPERATURE,
        api_key=Config.OPENROUTER_API_KEY,
        base_url=Config.OPENROUTER_BASE_URL,
        streaming=True
    )

    def token_stream():
        full_answer = ""
        try:
            for chunk in llm_stream.stream(prompt):
                token = chunk.content
                if token:
                    full_answer += token
                    yield f"data: {json.dumps({'token': token})}\n\n"
            cache.cache_response(cache_key, {"answer": full_answer, "sources": sources})
            yield f"data: {json.dumps({'done': True, 'sources': sources, 'cached': False})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(token_stream(), media_type="text/event-stream")