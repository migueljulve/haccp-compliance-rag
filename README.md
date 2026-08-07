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