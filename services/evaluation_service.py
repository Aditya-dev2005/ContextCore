"""
RAGAS-style Evaluation Service — LLM-as-judge implementation.

Metrics:
  - Precision@K, MRR, Hit Rate (retrieval quality)
  - Answer Relevance, Context Precision (generation quality)
"""

import re
from typing import List, Dict
from langchain_openai import ChatOpenAI
from config import Config


class RAGASEvaluator:
    def __init__(self):
        self.judge = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0.0,
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL,
        )

    def _judge_relevance(self, question: str, chunk: str) -> bool:
        prompt = f"""You are evaluating document retrieval quality.

Question: {question}

Retrieved Chunk:
{chunk}

Does this chunk contain information that helps answer the question?
Reply with ONLY one word: YES or NO."""
        try:
            resp = self.judge.invoke(prompt).content.strip().upper()
            return resp.startswith("YES")
        except Exception:
            return False

    def _judge_score(self, prompt: str) -> float:
        try:
            resp = self.judge.invoke(prompt).content.strip()
            match = re.search(r"(\d+(\.\d+)?)", resp)
            if match:
                score = float(match.group(1))
                return max(0.0, min(10.0, score))
        except Exception:
            pass
        return 5.0

    def precision_at_k(self, question: str, chunks: List[str]) -> Dict:
        if not chunks:
            return {"score": 0.0, "relevant_count": 0, "total": 0, "flags": []}
        relevant_flags = [self._judge_relevance(question, c) for c in chunks]
        relevant_count = sum(relevant_flags)
        return {
            "score": round(relevant_count / len(chunks), 4),
            "relevant_count": relevant_count,
            "total": len(chunks),
            "flags": relevant_flags,
        }

    def mrr_score(self, relevance_flags: List[bool]) -> float:
        for i, is_relevant in enumerate(relevance_flags):
            if is_relevant:
                return round(1.0 / (i + 1), 4)
        return 0.0

    def hit_rate(self, relevance_flags: List[bool]) -> float:
        return 1.0 if any(relevance_flags) else 0.0

    def answer_relevance(self, question: str, answer: str) -> float:
        prompt = f"""Rate how well this answer addresses the question, on a scale of 0 to 10.
0 = completely irrelevant or doesn't answer the question at all.
10 = perfectly and completely answers the question.

Question: {question}

Answer: {answer}

Reply with ONLY a single number between 0 and 10."""
        return self._judge_score(prompt)

    def context_precision(self, answer: str, context: str) -> float:
        prompt = f"""Rate how much of the following context was actually used/reflected
in the answer below, on a scale of 0 to 10.
0 = the answer ignores the context entirely.
10 = the answer makes full, precise use of the relevant context.

Context:
{context[:2000]}

Answer: {answer}

Reply with ONLY a single number between 0 and 10."""
        return self._judge_score(prompt)

    def evaluate(self, question: str, answer: str, retrieved_chunks: List[str]) -> Dict:
        precision_result = self.precision_at_k(question, retrieved_chunks)
        flags = precision_result.get("flags", [])

        mrr = self.mrr_score(flags)
        hit = self.hit_rate(flags)
        ans_rel = self.answer_relevance(question, answer)
        context_text = "\n\n".join(retrieved_chunks)
        ctx_prec = self.context_precision(answer, context_text)

        overall = (
            precision_result["score"] * 0.25
            + mrr * 0.20
            + hit * 0.15
            + (ans_rel / 10) * 0.25
            + (ctx_prec / 10) * 0.15
        )

        return {
            "precision_at_k": precision_result["score"],
            "mrr": mrr,
            "hit_rate": hit,
            "answer_relevance": round(ans_rel / 10, 4),
            "context_precision": round(ctx_prec / 10, 4),
            "overall_score": round(overall, 4),
            "details": {
                "relevant_chunks": precision_result["relevant_count"],
                "total_chunks": precision_result["total"],
            },
        }