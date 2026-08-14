"""Evaluate retrieval quality: hit-rate and MRR over ground truth questions.
Follows the same evaluate() pattern the course uses in rag-test.ipynb.
"""

import os

import pandas as pd
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

COLLECTION = "haccp"
MODEL_NAME = "multi-qa-mpnet-base-dot-v1"
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))


def hit_rate(relevance_total):
    cnt = 0
    for line in relevance_total:
        if True in line:
            cnt += 1
    return cnt / len(relevance_total)


def mrr(relevance_total):
    total_score = 0.0
    for line in relevance_total:
        for rank in range(len(line)):
            if line[rank]:
                total_score += 1 / (rank + 1)
    return total_score / len(relevance_total)


def evaluate(ground_truth, search_function):
    relevance_total = []
    for q in tqdm(ground_truth):
        doc_id = q["chunk_id"]
        results = search_function(q)
        relevance = [d["id"] == doc_id for d in results]
        relevance_total.append(relevance)
    return {"hit_rate": hit_rate(relevance_total), "mrr": mrr(relevance_total)}


def main():
    gt_df = pd.read_csv("data/ground_truth.csv")
    ground_truth = gt_df.to_dict(orient="records")

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    model = SentenceTransformer(MODEL_NAME)

    # Chunk ids are sequential 0..N-1 (assigned in ingest.py), so sorting by
    # id and indexing into the list lines the BM25 corpus up with real ids.
    points = client.scroll(collection_name=COLLECTION, limit=1000)[0]
    texts = [p.payload["text"] for p in sorted(points, key=lambda p: p.id)]
    bm25 = BM25Okapi([t.lower().split() for t in texts])

    def vector_search(q):
        vector = model.encode(q["question"]).tolist()
        hits = client.query_points(collection_name=COLLECTION, query=vector, limit=5).points
        return [{"id": h.id} for h in hits]

    def bm25_search(q):
        scores = bm25.get_scores(q["question"].lower().split())
        top_ids = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]
        return [{"id": i} for i in top_ids]

    def hybrid_search(q):
        vector = model.encode(q["question"]).tolist()
        vector_hits = client.query_points(collection_name=COLLECTION, query=vector, limit=20).points
        vector_ids = [h.id for h in vector_hits]

        scores = bm25.get_scores(q["question"].lower().split())
        bm25_ids = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:20]

        # Reciprocal Rank Fusion: a chunk ranking well in both lists rises to
        # the top, without needing cosine and BM25 scores to be comparable.
        rrf_scores = {}
        for rank, doc_id in enumerate(vector_ids):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (60 + rank)
        for rank, doc_id in enumerate(bm25_ids):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (60 + rank)

        top_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:5]
        return [{"id": i} for i in top_ids]

    print("vector:", evaluate(ground_truth, vector_search))
    print("bm25:  ", evaluate(ground_truth, bm25_search))
    print("hybrid:", evaluate(ground_truth, hybrid_search))


if __name__ == "__main__":
    main()

