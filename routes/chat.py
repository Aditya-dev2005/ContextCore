from fastapi import APIRouter, HTTPException
from models.schemas import QuestionRequest, QuestionResponse
from services.vector_store import get_vectorstore, similarity_search
from services.cache_service import CacheService
from config import Config
from langchain_openai import ChatOpenAI
import time
import hashlib

router = APIRouter()

# Initialize LLM
llm = ChatOpenAI(
    model=Config.LLM_MODEL,
    temperature=Config.TEMPERATURE,
    api_key=Config.OPENROUTER_API_KEY,
    base_url=Config.OPENROUTER_BASE_URL
)

# Initialize cache service
cache = CacheService()

def generate_cache_key(question: str) -> str:
    normalized = ' '.join(question.lower().split())
    return f"rag:q:{hashlib.md5(normalized.encode()).hexdigest()}"

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question about uploaded PDFs with Redis caching"""

    start_time = time.time()

    try:
        # 1. Check cache first
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

            prompt = f"""Answer the question as detailed as possible from the provided context.
If the answer is not in the context, just say: "Answer is not available in the context."

Context:
{context}

Question:
{request.question}

Answer:"""

            response = llm.invoke(prompt)
            answer = response.content

        # 4. Cache the response
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