"""
Semantic Cache — embedding-based cache that catches paraphrased questions.

Two-level lookup:
  1. Exact match  — md5 hash of normalized question (instant, cheapest)
  2. Semantic match — cosine similarity over sentence embeddings (catches
     "What is the leave policy?" vs "Tell me about leave policy" as the
     same cached answer)

Falls back gracefully — if sentence-transformers isn't installed, or Redis
is unavailable, the cache simply no-ops and the app behaves exactly like
before (always calls the LLM).
"""

import json
import hashlib
import time
from typing import Optional

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False

SIMILARITY_THRESHOLD = 0.92   # cosine similarity cutoff for a "hit"
MAX_ENTRIES_PER_USER = 500    # cap so the index list never grows unbounded

_model = None


def _get_model():
    """Lazy-load the embedding model — avoids slowing down server startup."""
    global _model
    if _model is None and SEMANTIC_AVAILABLE:
        print("⏳ Loading semantic cache embedding model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Semantic cache model ready")
    return _model


def _cosine_similarity(a, b) -> float:
    a, b = np.array(a), np.array(b)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


class SemanticCache:
    def __init__(self, redis_client=None, ttl: int = 3600):
        self.client = redis_client
        self.ttl = ttl
        self.enabled = SEMANTIC_AVAILABLE and self.client is not None
        if not SEMANTIC_AVAILABLE:
            print("⚠️ sentence-transformers not installed — semantic cache disabled (exact-match only)")

    def _exact_key(self, user: str, question: str) -> str:
        normalized = " ".join(question.lower().split())
        h = hashlib.md5(normalized.encode()).hexdigest()
        return f"sem:exact:{user}:{h}"

    def _index_key(self, user: str) -> str:
        return f"sem:index:{user}"

    def _entry_key(self, user: str, entry_id: str) -> str:
        return f"sem:entry:{user}:{entry_id}"

    # ── Public API ──────────────────────────────────────────────────────
    def get(self, user: str, question: str) -> Optional[dict]:
        """Returns cached response dict if a semantic or exact match is found."""
        if not self.client:
            return None

        # 1) Exact match — cheap, instant
        try:
            exact = self.client.get(self._exact_key(user, question))
            if exact:
                data = json.loads(exact)
                data["_cache_type"] = "exact"
                return data
        except Exception:
            pass

        # 2) Semantic match — only if embeddings are available
        if not self.enabled:
            return None

        try:
            model = _get_model()
            query_emb = model.encode(question).tolist()

            entry_ids = self.client.lrange(self._index_key(user), 0, -1)
            best_score, best_entry = 0.0, None

            for entry_id in entry_ids:
                raw = self.client.get(self._entry_key(user, entry_id))
                if not raw:
                    continue
                entry = json.loads(raw)
                score = _cosine_similarity(query_emb, entry["embedding"])
                if score > best_score:
                    best_score, best_entry = score, entry

            if best_entry and best_score >= SIMILARITY_THRESHOLD:
                best_entry["_cache_type"] = "semantic"
                best_entry["_similarity"] = round(best_score, 4)
                return best_entry
        except Exception as e:
            print(f"⚠️ Semantic cache lookup failed: {e}")

        return None

    def set(self, user: str, question: str, response: dict):
        """Stores response under both exact key and semantic index."""
        if not self.client:
            return

        payload = {"answer": response.get("answer"), "sources": response.get("sources", [])}

        # Exact-match entry
        try:
            self.client.setex(self._exact_key(user, question), self.ttl, json.dumps(payload))
        except Exception:
            pass

        # Semantic entry
        if not self.enabled:
            return
        try:
            model = _get_model()
            embedding = model.encode(question).tolist()
            entry_id = hashlib.md5(f"{question}{time.time()}".encode()).hexdigest()[:12]

            entry = {**payload, "question": question, "embedding": embedding}
            self.client.setex(self._entry_key(user, entry_id), self.ttl, json.dumps(entry))

            idx_key = self._index_key(user)
            self.client.lpush(idx_key, entry_id)
            self.client.ltrim(idx_key, 0, MAX_ENTRIES_PER_USER - 1)
            self.client.expire(idx_key, self.ttl)
        except Exception as e:
            print(f"⚠️ Semantic cache write failed: {e}")

    def clear(self, user: str):
        if not self.client:
            return
        try:
            entry_ids = self.client.lrange(self._index_key(user), 0, -1)
            for eid in entry_ids:
                self.client.delete(self._entry_key(user, eid))
            self.client.delete(self._index_key(user))
            for key in self.client.scan_iter(f"sem:exact:{user}:*"):
                self.client.delete(key)
        except Exception:
            pass