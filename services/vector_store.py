from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config import Config
from typing import List, Optional, Dict

_embeddings: Optional[OpenAIEmbeddings] = None

# Per-user vectorstores: { username: FAISS }
_user_stores: Dict[str, FAISS] = {}

DEFAULT_USER = "__default__"


def get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL
        )
    return _embeddings


def add_to_vectorstore(chunks: List[str], filename: str, user: str = DEFAULT_USER):
    """Add documents to a user-specific vectorstore."""
    global _user_stores
    docs = [
        Document(page_content=chunk, metadata={"source": filename})
        for chunk in chunks
    ]
    if user not in _user_stores:
        _user_stores[user] = FAISS.from_documents(docs, get_embeddings())
    else:
        _user_stores[user].add_documents(docs)
    return _user_stores[user]


def get_vectorstore(user: str = DEFAULT_USER) -> Optional[FAISS]:
    return _user_stores.get(user)


def clear_vectorstore(user: str = DEFAULT_USER):
    if user in _user_stores:
        del _user_stores[user]


def similarity_search(query: str, k: int = 4, user: str = DEFAULT_USER) -> list:
    store = _user_stores.get(user)
    if store is None:
        return []
    return store.similarity_search(query, k=k)