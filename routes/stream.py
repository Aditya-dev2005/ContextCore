from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models.schemas import QuestionRequest
from services.vector_store import get_vectorstore, similarity_search
from services.cache_service import CacheService
from config import Config
from langchain_openai import ChatOpenAI
import json
import time

router = APIRouter()

cache = CacheService()

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


@router.post("/stream")
async def stream_answer(request: QuestionRequest):
    # Check cache first — agar cache hit hai toh stream karke bhejo
    cached = cache.get_cached_response(request.question)
    if cached:
        print("⚡ Redis CACHE HIT (stream)!")
        answer = cached["answer"]
        sources = cached.get("sources", [])

        def cached_stream():
            # Token by token stream karo cached answer
            words = answer.split(" ")
            for i, word in enumerate(words):
                chunk = word if i == 0 else " " + word
                yield f"data: {json.dumps({'token': chunk})}\n\n"
            # Sources at the end
            yield f"data: {json.dumps({'done': True, 'sources': sources, 'cached': True})}\n\n"

        return StreamingResponse(cached_stream(), media_type="text/event-stream")

    # Vector store check
    vectorstore = get_vectorstore()
    if vectorstore is None:
        raise HTTPException(
            status_code=400,
            detail="No documents indexed yet. Please upload PDFs first."
        )

    docs = similarity_search(request.question, k=4)

    if not docs:
        def no_docs_stream():
            msg = "No relevant information found in the uploaded documents."
            yield f"data: {json.dumps({'token': msg})}\n\n"
            yield f"data: {json.dumps({'done': True, 'sources': []})}\n\n"
        return StreamingResponse(no_docs_stream(), media_type="text/event-stream")

    context = "\n\n".join([doc.page_content for doc in docs])
    sources = list(set([doc.metadata.get("source", "unknown") for doc in docs]))
    prompt = build_prompt(context, request.question, request.conversation_history or [])

    # Streaming LLM
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

            # Cache karo complete answer
            cache.cache_response(request.question, {"answer": full_answer, "sources": sources})

            # Done signal with sources
            yield f"data: {json.dumps({'done': True, 'sources': sources, 'cached': False})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(token_stream(), media_type="text/event-stream")