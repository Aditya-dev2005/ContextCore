from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config import Config
from typing import List, Optional

# Lazy-loaded — NOT initialized at import time
_embeddings: Optional[OpenAIEmbeddings] = None
_vectorstore: Optional[FAISS] = None


def get_embeddings() -> OpenAIEmbeddings:
    """Initialize embeddings only when first needed, not at startup."""
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL
        )
    return _embeddings


def add_to_vectorstore(chunks: List[str], filename: str):
    """First upload creates index, subsequent uploads merge into it."""
    global _vectorstore
    docs = [
        Document(page_content=chunk, metadata={"source": filename})
        for chunk in chunks
    ]
    if _vectorstore is None:
        _vectorstore = FAISS.from_documents(docs, get_embeddings())
    else:
        _vectorstore.add_documents(docs)
    return _vectorstore


def get_vectorstore() -> Optional[FAISS]:
    return _vectorstore


def clear_vectorstore():
    global _vectorstore
    _vectorstore = None


def similarity_search(query: str, k: int = 4) -> list:
    if _vectorstore is None:
        return []
    return _vectorstore.similarity_search(query, k=k)