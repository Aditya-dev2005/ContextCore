from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config import Config
from typing import List, Optional

# Initialize embeddings
embeddings = OpenAIEmbeddings(
    model=Config.EMBEDDING_MODEL,
    api_key=Config.OPENROUTER_API_KEY,
    base_url=Config.OPENROUTER_BASE_URL
)

# ── In-memory singleton ───────────────────────────────────────
# This persists across requests for the lifetime of the server.
# All uploaded PDFs accumulate here — never overwritten.
_vectorstore: Optional[FAISS] = None


def add_to_vectorstore(chunks: List[str], filename: str):
    """
    Add chunks from a new PDF into the shared FAISS index.
    - First upload  → creates a fresh index
    - Every subsequent upload → merges into the existing index
    """
    global _vectorstore

    docs = [
        Document(
            page_content=chunk,
            metadata={"source": filename}   # track which PDF each chunk came from
        )
        for chunk in chunks
    ]

    if _vectorstore is None:
        # First document — build index from scratch
        _vectorstore = FAISS.from_documents(docs, embeddings)
    else:
        # Subsequent documents — merge into existing index
        _vectorstore.add_documents(docs)

    return _vectorstore


def get_vectorstore() -> Optional[FAISS]:
    """Return the current shared index, or None if nothing indexed yet."""
    return _vectorstore


def clear_vectorstore():
    """Wipe the in-memory index (called when user clicks 'Clear docs')."""
    global _vectorstore
    _vectorstore = None


def similarity_search(query: str, k: int = 4):
    """
    Search the shared index.
    Returns empty list if nothing has been indexed yet.
    """
    if _vectorstore is None:
        return []
    return _vectorstore.similarity_search(query, k=k)