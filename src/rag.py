"""RAG pipeline: hybrid search + prompt building + Gemini generation + relevance eval."""

import json
import os
from time import time, sleep

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

load_dotenv()

COLLECTION = "haccp"
EMBEDDING_MODEL = "multi-qa-mpnet-base-dot-v1"
LLM_MODEL = "gemini-3.5-flash-lite"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embedding_model = SentenceTransformer(EMBEDDING_MODEL)
llm_client = OpenAI(api_key=os.getenv("GEMINI_API_KEY"), base_url=BASE_URL)

points = qdrant.scroll(collection_name=COLLECTION, limit=1000)[0]
chunks = {p.id: p.payload for p in points}
bm25 = BM25Okapi([chunks[i]["text"].lower().split() for i in sorted(chunks)])


def search(query, k=5, rrf_k=60):
    """Hybrid search: fuse vector + BM25 top-20 via RRF, return the top-k chunks."""
    vector = embedding_model.encode(query).tolist()
    vector_hits = qdrant.query_points(collection_name=COLLECTION, query=vector, limit=20).points
    vector_ids = [h.id for h in vector_hits]

    scores = bm25.get_scores(query.lower().split())
    bm25_ids = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:20]

    rrf_scores = {}
    for rank, doc_id in enumerate(vector_ids):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (rrf_k + rank)
    for rank, doc_id in enumerate(bm25_ids):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (rrf_k + rank)

    top_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:k]
    return [chunks[i] for i in top_ids]


prompt_template = """
You are a HACCP food safety compliance assistant. Answer the QUESTION based on the CONTEXT below,
which comes from Codex Alimentarius and FDA/USDA regulatory sources. Use only the facts from the
CONTEXT. Cite the source of each fact using its citation (e.g. "21 CFR 123 § 123.6").
If the CONTEXT does not contain the answer, say so explicitly instead of guessing.

QUESTION: {question}

CONTEXT:
{context}
""".strip()

entry_template = """
Source: {citation}
{text}
""".strip()


def build_prompt(query, search_results):
    context = "\n\n".join(entry_template.format(**doc) for doc in search_results)
    return prompt_template.format(question=query, context=context)


def llm(prompt, model=LLM_MODEL):
    for _ in range(6):
        try:
            response = llm_client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": prompt}]
            )
            answer = response.choices[0].message.content
            token_stats = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            return answer, token_stats
        except RateLimitError:
            sleep(20)
    raise RuntimeError(f"LLM call failed after retries (model={model})")


evaluation_prompt_template = """
You are an expert evaluator for a RAG system that answers HACCP food safety compliance questions.
Your task is to analyze the relevance of the generated answer to the given question.
Classify it as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

Question: {question}
Generated Answer: {answer}

Return parsable JSON without code blocks:
{{"Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT", "Explanation": "..."}}
""".strip()


def evaluate_relevance(question, answer):
    prompt = evaluation_prompt_template.format(question=question, answer=answer)
    evaluation, tokens = llm(prompt)
    try:
        return json.loads(evaluation), tokens
    except json.JSONDecodeError:
        return {"Relevance": "UNKNOWN", "Explanation": "Failed to parse evaluation"}, tokens


def rag(query, model=LLM_MODEL):
    t0 = time()

    search_results = search(query)
    prompt = build_prompt(query, search_results)
    answer, token_stats = llm(prompt, model=model)
    relevance, rel_token_stats = evaluate_relevance(query, answer)

    took = time() - t0

    return {
        "answer": answer,
        "model_used": model,
        "response_time": took,
        "relevance": relevance.get("Relevance", "UNKNOWN"),
        "relevance_explanation": relevance.get("Explanation", "Failed to parse evaluation"),
        "prompt_tokens": token_stats["prompt_tokens"],
        "completion_tokens": token_stats["completion_tokens"],
        "total_tokens": token_stats["total_tokens"],
        "eval_prompt_tokens": rel_token_stats["prompt_tokens"],
        "eval_completion_tokens": rel_token_stats["completion_tokens"],
        "eval_total_tokens": rel_token_stats["total_tokens"],
        # Gemini free tier: real cost is $0.
        "cost_usd": 0.0,
    }


if __name__ == "__main__":
    result = rag("What is a critical control point?")
    print(json.dumps(result, indent=2))
