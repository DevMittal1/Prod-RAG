# End-to-End Production RAG Documentation

This backend is a modular Retrieval-Augmented Generation system built around FastAPI, Celery workers, Gemini embeddings and generation, Qdrant hybrid search, Redis memory, guardrails, observability hooks, and evaluation endpoints.

See [architecture.md](/Users/dev/Documents/resume-projects/productionRAG/docs/architecture.md) for the visual diagram.

## System Goals

- Serve grounded answers from enterprise documents.
- Support tenant-aware and metadata-aware retrieval.
- Use hybrid retrieval: dense semantic search plus sparse lexical search inside Qdrant.
- Improve retrieval quality with rank fusion and optional cross-encoder reranking.
- Keep ingestion asynchronous so API requests stay responsive.
- Keep provider integrations behind small adapters so the system can evolve.
- Provide observability and evaluation hooks from the start.

## High-Level Components

| Layer | Implementation | Purpose |
| --- | --- | --- |
| API | [app/main.py](/Users/dev/Documents/resume-projects/productionRAG/app/main.py), [app/api/v1](/Users/dev/Documents/resume-projects/productionRAG/app/api/v1) | HTTP interface for query, ingestion, jobs, and evaluation |
| Pipeline | [app/rag/pipeline.py](/Users/dev/Documents/resume-projects/productionRAG/app/rag/pipeline.py) | Orchestrates the online RAG request lifecycle |
| Embeddings | [app/rag/embeddings.py](/Users/dev/Documents/resume-projects/productionRAG/app/rag/embeddings.py) | Creates Gemini query/document vectors |
| Retrieval | [app/rag/retrievers.py](/Users/dev/Documents/resume-projects/productionRAG/app/rag/retrievers.py) | Runs Qdrant built-in hybrid search over named dense and sparse vectors |
| Fusion | Qdrant Query API | Merges dense and sparse results with built-in reciprocal rank fusion |
| Reranking | [app/rag/rerankers.py](/Users/dev/Documents/resume-projects/productionRAG/app/rag/rerankers.py) | Optionally reranks retrieved chunks with a cross-encoder |
| LLM | [app/rag/llm.py](/Users/dev/Documents/resume-projects/productionRAG/app/rag/llm.py) | Generates grounded answers with Gemini |
| Ingestion | [app/ingestion](/Users/dev/Documents/resume-projects/productionRAG/app/ingestion) | Chunks documents and indexes dense/sparse vectors into Qdrant |
| Workers | [app/workers](/Users/dev/Documents/resume-projects/productionRAG/app/workers) | Runs ingestion asynchronously through Celery |
| Memory | [app/memory/redis_memory.py](/Users/dev/Documents/resume-projects/productionRAG/app/memory/redis_memory.py) | Stores recent chat turns in Redis |
| Guardrails | [app/guardrails/policy.py](/Users/dev/Documents/resume-projects/productionRAG/app/guardrails/policy.py) | Validates user input and model output |
| Observability | [app/observability](/Users/dev/Documents/resume-projects/productionRAG/app/observability) | Emits structured logs, OpenTelemetry traces, and optional Langfuse traces |
| Evaluation | [app/evaluation/rag.py](/Users/dev/Documents/resume-projects/productionRAG/app/evaluation/rag.py) | Provides lightweight RAG quality scoring hooks |

## Request Lifecycle

### 1. Document Ingestion

Documents enter through `POST /api/v1/documents`.

1. FastAPI receives a `DocumentIngestRequest`.
2. The route enqueues `ingest_documents` as a Celery task.
3. Celery stores the task in Redis.
4. A worker loads the request and enriches each document with `tenant_id`.
5. Documents are split into overlapping chunks by `chunk_document`.
6. Chunks are embedded with Gemini using `task_type="RETRIEVAL_DOCUMENT"`.
7. The worker writes each chunk's dense and sparse vectors into Qdrant.
8. Qdrant payload indexes support fast filtering on tenant, department, role, and tags.
9. Job state can be queried through `GET /api/v1/jobs/{job_id}`.

The ingestion path is intentionally separate from the query path. This keeps large document processing, embedding calls, and indexing work out of the user-facing request cycle.

### 2. Online Query

Queries enter through `POST /api/v1/query`.

1. FastAPI validates the request schema.
2. `RAGPipeline.answer()` starts a trace.
3. Input guardrails reject unsafe or policy-violating prompts.
4. Redis memory loads recent turns for the user/session pair.
5. Gemini embeds the user query using `task_type="RETRIEVAL_QUERY"`.
6. Qdrant retrieves semantically similar chunks.
7. Qdrant sparse vector retrieval finds lexical matches.
8. Metadata filters restrict retrieval by tenant, department, role, and tags.
9. Qdrant's Query API merges dense and sparse result lists with reciprocal rank fusion.
10. The optional reranker reorders the merged list for precision.
11. Gemini generates an answer using only the selected context.
12. Output guardrails validate the model response.
13. Redis memory stores the new query/answer turn.
14. Observability hooks record the trace.
15. The API returns the answer, retrieved chunks, and trace ID.

## Data Models

### Query Request

```json
{
  "query": "What is our refund policy?",
  "user_id": "user-123",
  "session_id": "session-abc",
  "filters": {
    "tenant_id": "acme",
    "department": "support",
    "role": "agent",
    "tags": ["policy"]
  },
  "top_k": 8
}
```

### Query Response

```json
{
  "answer": "The refund policy is ...",
  "chunks": [
    {
      "id": "doc-1:0",
      "text": "Relevant source chunk...",
      "score": 0.032,
      "source": "refund-policy.pdf",
      "metadata": {
        "tenant_id": "acme",
        "department": "support"
      }
    }
  ],
  "trace_id": "generated-trace-id"
}
```

### Ingest Request

```json
{
  "tenant_id": "acme",
  "documents": [
    {
      "id": "refund-policy",
      "text": "Full document text...",
      "source": "refund-policy.pdf",
      "metadata": {
        "department": "support",
        "tags": ["policy"]
      }
    }
  ]
}
```

## Configuration

Configuration is loaded from environment variables through [app/core/config.py](/Users/dev/Documents/resume-projects/productionRAG/app/core/config.py). Start from [.env.example](/Users/dev/Documents/resume-projects/productionRAG/.env.example).

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `Production RAG` | Service name |
| `ENVIRONMENT` | `local` | Runtime environment label |
| `LOG_LEVEL` | `INFO` | Structured logging level |
| `GEMINI_API_KEY` | empty | Gemini API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Generation model |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | Embedding model |
| `GEMINI_EMBEDDING_DIMENSIONS` | `768` | Qdrant vector size and Gemini output dimensionality |
| `REDIS_URL` | `redis://localhost:6379/0` | Session memory Redis DB |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | Celery task result backend |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant URL |
| `QDRANT_API_KEY` | `api_key` | Qdrant API key |
| `QDRANT_COLLECTION` | `documents` | Qdrant collection name |
| `LANGFUSE_PUBLIC_KEY` | empty | Optional Langfuse public key |
| `LANGFUSE_SECRET_KEY` | empty | Optional Langfuse secret key |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Langfuse host |
| `TOP_K_DENSE` | `30` | Dense retrieval candidate count |
| `TOP_K_SPARSE` | `30` | Sparse retrieval candidate count |
| `TOP_K_FINAL` | `8` | Final chunks sent to generation |

Important: if `GEMINI_EMBEDDING_DIMENSIONS` changes after the Qdrant collection exists, recreate the collection or migrate vectors. Qdrant collections require a fixed vector size.

If you are migrating from the previous OpenSearch-backed scaffold, recreate the Qdrant collection so it has the named vectors `dense` and `sparse`.

## Local Development

### Start Dependencies

```bash
cp .env.example .env
# Fill GEMINI_API_KEY in .env
docker compose up -d redis qdrant
```

### Install Python Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Install reranking dependencies only when you want local cross-encoder reranking:

```bash
pip install -e ".[rerank]"
```

### Run API

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Run Worker

```bash
celery -A app.workers.celery_app worker --loglevel=INFO
```

### Run Tests

```bash
pytest -q
```

## API Usage

### Health

```bash
curl http://localhost:8000/health
```

### Ingest Documents

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "acme",
    "documents": [
      {
        "id": "handbook-1",
        "text": "Employees can request reimbursement within 30 days.",
        "source": "handbook.md",
        "metadata": {
          "department": "finance",
          "tags": ["reimbursement"]
        }
      }
    ]
  }'
```

### Check Job

```bash
curl http://localhost:8000/api/v1/jobs/<job_id>
```

### Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How long do employees have to request reimbursement?",
    "user_id": "user-1",
    "session_id": "session-1",
    "filters": {
      "tenant_id": "acme",
      "department": "finance",
      "tags": ["reimbursement"]
    },
    "top_k": 5
  }'
```

### Evaluate a RAG Sample

```bash
curl -X POST http://localhost:8000/api/v1/evaluations/rag \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How long do employees have to request reimbursement?",
    "answer": "Employees have 30 days to request reimbursement.",
    "contexts": ["Employees can request reimbursement within 30 days."],
    "reference_answer": "Employees can request reimbursement within 30 days."
  }'
```

## Retrieval Design

Dense retrieval handles semantic similarity. Sparse retrieval handles exact terms, identifiers, acronyms, codes, and proper nouns. The system stores both vector types in Qdrant and uses Qdrant's Query API to prefetch both result sets and merge them with reciprocal rank fusion.

The built-in Qdrant fusion mode is reciprocal rank fusion:

```text
score(document) = sum(1 / (k + rank_in_result_set))
```

This makes documents that appear in both dense and sparse retrieval rank higher without requiring dense and sparse scores to share the same scale.

## Metadata Filtering

Filters are accepted through `MetadataFilter`:

- `tenant_id`
- `department`
- `role`
- `tags`
- `extra`

The hybrid retriever converts filters to Qdrant filter conditions and applies them to dense and sparse prefetches.

The indexer creates Qdrant payload indexes for `metadata.tenant_id`, `metadata.department`, `metadata.role`, and `metadata.tags` when it creates the collection.

For enterprise deployments, `tenant_id` should be required at the auth boundary, not trusted only from the request body. A common production pattern is to resolve tenant and role claims from JWT/session middleware, then inject filters server-side.

## Gemini Embedding Strategy

The system intentionally uses different task types:

- Query embeddings: `RETRIEVAL_QUERY`
- Document embeddings: `RETRIEVAL_DOCUMENT`

This matches Gemini's retrieval optimization pattern and keeps document vectors and query vectors in the same retrieval space while allowing task-specific behavior.

The default `GEMINI_EMBEDDING_DIMENSIONS=768` is a production-friendly balance between quality, storage, and latency.

## Memory

Redis stores recent turns under:

```text
chat:{user_id}:{session_id}
```

The current implementation keeps the latest 20 messages and expires sessions after seven days. This is short-term memory for conversation continuity. Long-term semantic memory can be added as a separate vector collection or PostgreSQL table.

## Guardrails

The current guardrail layer is intentionally small:

- Reject known prompt-injection phrases.
- Reject empty model outputs.

Production extensions can add:

- PII detection.
- Tenant leakage checks.
- Allow/deny topics.
- Structured output validation.
- Llama Guard or NeMo Guardrails integration.
- Citation coverage checks before returning an answer.

## Observability

The app emits structured JSON logs through `structlog`. OpenTelemetry is configured with service metadata. Langfuse tracing is optional and activates when `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set.

Recommended production metrics:

- API latency by endpoint.
- Retrieval latency by backend.
- Gemini embedding and generation latency.
- Token usage and model cost.
- Qdrant error rate.
- Celery queue depth.
- Ingestion throughput.
- Reranker latency.
- Cache hit ratio.
- Context precision and faithfulness from eval jobs.

## Evaluation

The current evaluation endpoint provides lightweight lexical scores:

- `faithfulness`
- `context_precision`
- `answer_relevance`

This is a placeholder for full CI/CD evaluation with tools such as RAGAS, DeepEval, Phoenix, or LangSmith. A stronger evaluation pipeline should run curated question sets after retrieval/prompt changes and before deployment.

## Deployment Notes

The repository includes [Dockerfile](/Users/dev/Documents/resume-projects/productionRAG/Dockerfile) and [docker-compose.yml](/Users/dev/Documents/resume-projects/productionRAG/docker-compose.yml).

For production:

- Run API and workers as separate deployments.
- Scale API replicas horizontally behind a load balancer.
- Scale Celery workers based on ingestion volume.
- Use managed Redis and Qdrant where possible.
- Store secrets in a cloud secret manager, not `.env` files.
- Add authentication and tenant resolution middleware.
- Add rate limits per tenant/user.
- Add retries and dead-letter queues for ingestion failures.
- Add dashboards and alerts for latency, error rate, queue depth, and cost.
- Pin model versions and run evals before model upgrades.

## Extension Points

| Goal | Where to Extend |
| --- | --- |
| Add auth/RBAC | FastAPI middleware and route dependencies |
| Add new vector DB | Replace `HybridRetriever` in `app/rag/retrievers.py` |
| Change sparse vectorization | Extend `app/rag/sparse.py` |
| Add reranker provider | Extend `app/rag/rerankers.py` |
| Add semantic cache | Add cache lookup before retrieval/generation in `RAGPipeline.answer()` |
| Add document loaders | Add loaders before `DocumentIngestRequest` or worker chunking |
| Add long-term memory | Add vector/SQL memory store beside Redis session memory |
| Add eval CI | Add pytest/CI jobs that call evaluation datasets |
| Add stricter guardrails | Extend `GuardrailService` |
| Add tracing exporter | Extend `app/observability/tracing.py` |

## Operational Checklist

- `GEMINI_API_KEY` is set.
- Qdrant is reachable from API and worker.
- Qdrant collection vector size matches `GEMINI_EMBEDDING_DIMENSIONS`.
- API process and worker process run separately.
- Celery broker and result backend point to Redis.
- Tenant filters are applied for every enterprise query.
- Ingestion jobs are monitored.
- Retrieval and generation latency are tracked.
- Evaluation sets run before retrieval, prompt, model, or chunking changes.
