from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.upload import router as upload_router
from routes.chat import router as chat_router
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Enterprise RAG Platform",
    description="Production-ready RAG system for PDF Q&A",
    version="1.0.0"
)

# Configure CORS for Flutter frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router, prefix="/api", tags=["upload"])
app.include_router(chat_router, prefix="/api", tags=["chat"])

@app.get("/")
async def root():
    return {
        "message": "Enterprise RAG Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)