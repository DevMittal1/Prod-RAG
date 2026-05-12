# Production RAG Backend

Modular FastAPI backend for enterprise RAG with async workers, hybrid retrieval, metadata filtering, reranking, memory, observability, guardrails, and evaluation hooks.

## Stack

- API: FastAPI
- Workers: Celery + Redis
- LLM + embeddings: Gemini API via `google-genai`
- Hybrid search: Qdrant named dense/sparse vectors with built-in RRF fusion
- Memory: Redis adapter
- Orchestration: service graph in `app/rag/pipeline.py`
- Observability: OpenTelemetry + optional Langfuse
- Evaluation: lightweight local evaluator hooks, ready for RAGAS/DeepEval

## Quick Start

```bash
cp .env.example .env
# Fill GEMINI_API_KEY in .env
docker compose up -d redis qdrant
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Run a worker in another terminal:

```bash
celery -A app.workers.celery_app worker --loglevel=INFO
```

## API

- `GET /health`
- `POST /api/v1/query`
- `POST /api/v1/documents`
- `GET /api/v1/jobs/{job_id}`
- `POST /api/v1/evaluations/rag`

## Architecture

See [docs/architecture.md](/Users/dev/Documents/resume-projects/productionRAG/docs/architecture.md) for the end-to-end RAG architecture diagram.
See [docs/end-to-end.md](/Users/dev/Documents/resume-projects/productionRAG/docs/end-to-end.md) for the full engineering documentation and runbook.

## Gemini Embeddings

Document ingestion uses `task_type="RETRIEVAL_DOCUMENT"` and query retrieval uses `task_type="RETRIEVAL_QUERY"`. The default vector size is `GEMINI_EMBEDDING_DIMENSIONS=768`; if you change it after creating a Qdrant collection, recreate the collection so the stored vector size matches.
