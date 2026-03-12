from fastapi import APIRouter, HTTPException
from models.schemas import QuestionRequest, QuestionResponse
from services.vector_store import load_vectorstore, similarity_search
from config import Config
from langchain_openai import ChatOpenAI
import time

router = APIRouter()

# Initialize LLM
llm = ChatOpenAI(
    model=Config.LLM_MODEL,
    temperature=Config.TEMPERATURE,
    api_key=Config.OPENROUTER_API_KEY,
    base_url=Config.OPENROUTER_BASE_URL
)

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question about uploaded PDFs"""
    
    start_time = time.time()
    
    try:
        # Load vector store
        vectorstore = load_vectorstore()
        
        # Search for relevant documents
        docs = similarity_search(vectorstore, request.question, k=3)
        
        # Prepare context
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = list(set([doc.metadata.get("source", "unknown") for doc in docs]))
        
        # Create prompt
        prompt = f"""Answer the question as detailed as possible from the provided context.
If the answer is not in the context, just say: "Answer is not available in the context."

Context:
{context}

Question:
{request.question}

Answer:"""
        
        # Get response from LLM
        response = llm.invoke(prompt)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        return QuestionResponse(
            answer=response.content,
            sources=sources,
            latency_ms=round(latency_ms, 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))