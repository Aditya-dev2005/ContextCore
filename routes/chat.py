from fastapi import APIRouter, HTTPException
from models.schemas import QuestionRequest, QuestionResponse
from services.vector_store import get_vectorstore, similarity_search
from services.cache_service import CacheService
from config import Config
from langchain_openai import ChatOpenAI
import time
import hashlib

router = APIRouter()

llm = ChatOpenAI(
    model=Config.LLM_MODEL,
    temperature=Config.TEMPERATURE,
    api_key=Config.OPENROUTER_API_KEY,
    base_url=Config.OPENROUTER_BASE_URL
)

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

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    start_time = time.time()

    try:
        # 1. Always check cache by question text only
        #    Same question = cache hit, regardless of history
        cached_response = cache.get_cached_response(request.question)
        if cached_response:
            print("⚡ Redis CACHE HIT!")
            latency_ms = (time.time() - start_time) * 1000
            return QuestionResponse(
                answer=cached_response["answer"],
                sources=cached_response.get("sources", []),
                latency_ms=round(latency_ms, 2)
            )

        print("❌ Redis CACHE MISS - querying vector store")

        # 2. Get shared in-memory index
        vectorstore = get_vectorstore()
        if vectorstore is None:
            raise HTTPException(
                status_code=400,
                detail="No documents indexed yet. Please upload PDFs first."
            )

        # 3. Search across ALL indexed documents
        docs = similarity_search(request.question, k=4)

        if not docs:
            answer = "No relevant information found in the uploaded documents."
            sources = []
        else:
            context = "\n\n".join([doc.page_content for doc in docs])
            sources = list(set([doc.metadata.get("source", "unknown") for doc in docs]))

            # 4. Build prompt with conversation history
            prompt = build_prompt(context, request.question, request.conversation_history or [])
            response = llm.invoke(prompt)
            answer = response.content

        # 5. Cache the response
        cache.cache_response(request.question, {"answer": answer, "sources": sources})

        latency_ms = (time.time() - start_time) * 1000

        return QuestionResponse(
            answer=answer,
            sources=sources,
            latency_ms=round(latency_ms, 2)
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in ask_question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")