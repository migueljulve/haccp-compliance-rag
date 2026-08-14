# HACCP Food Safety Compliance RAG

Final project for the [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp). A RAG system
that answers HACCP / food safety compliance questions, grounded in the Codex Alimentarius HACCP
principles and FDA/USDA regulatory guidance.

> Status: in progress. See `CLAUDE.md` for the working plan and technical decisions (local notes,
> not part of this repo's history).

## Problem

*(To be completed once the corpus and pipeline are built.)*

## Stack

- **Data**: Codex Alimentarius (HACCP General Principles, CXC 1-1969) + FDA (21 CFR 120/123) +
  USDA FSIS guidance
- **Embeddings**: sentence-transformers (local)
- **Vector store**: Qdrant
- **LLM**: OpenAI API
- **Interface**: Streamlit
- **Monitoring**: Postgres + Grafana
- **Containerization**: docker-compose

## Retrieval Evaluation

Three retrieval methods were compared on 424 LLM-generated ground truth questions
(hit-rate@5 and MRR@5):

| Method | Hit Rate@5 | MRR@5 |
|---|---|---|
| Vector search | 0.764 | 0.585 |
| BM25 | 0.818 | 0.657 |
| **Hybrid (RRF)** | **0.844** | **0.680** |

Hybrid search (Reciprocal Rank Fusion over vector + BM25 top-20) wins on both
metrics and is the method used in the app. See `src/evaluate_retrieval.py`.

## Running the project

*(To be completed in the reproducibility phase.)*

## Structure

```
data/
  raw/          # raw source documents
  processed/    # cleaned and chunked data
src/
  ingestion/    # fetching, cleaning, loading into the vector store
  rag/          # retrieval + generation
  eval/         # retrieval and LLM evaluation
app/            # Streamlit interface
docker/         # containerization config
notebooks/      # exploration and evaluation
tests/          # tests
```