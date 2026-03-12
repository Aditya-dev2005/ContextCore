from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document  # <- यह change किया
from config import Config
from typing import List, Optional
import os

# Initialize embeddings
embeddings = OpenAIEmbeddings(
    model=Config.EMBEDDING_MODEL,
    api_key=Config.OPENROUTER_API_KEY,
    base_url=Config.OPENROUTER_BASE_URL
)

def create_vectorstore(chunks: List[str], metadata: Optional[dict] = None):
    """Create FAISS vector store from text chunks"""
    docs = [Document(page_content=chunk, metadata=metadata or {}) for chunk in chunks]
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore

def save_vectorstore(vectorstore, path: str = Config.FAISS_INDEX_PATH):
    """Save vector store to disk"""
    vectorstore.save_local(path)

def load_vectorstore(path: str = Config.FAISS_INDEX_PATH):
    """Load vector store from disk"""
    return FAISS.load_local(
        path,
        embeddings,
        allow_dangerous_deserialization=True
    )

def similarity_search(vectorstore, query: str, k: int = 3):
    """Search for similar documents"""
    return vectorstore.similarity_search(query, k=k)