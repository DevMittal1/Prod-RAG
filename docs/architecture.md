# End-to-End Legal Document Architecture

For the full system guide, see [end-to-end.md](/Users/dev/Documents/resume-projects/productionRAG/docs/end-to-end.md).

```mermaid
flowchart TB
    user[Client / App User]
    legalUser[Legal / Compliance User]
    api[FastAPI API<br/>app/main.py]
    authRoute[Auth APIs<br/>/api/v1/auth]
    queryRoute[POST /api/v1/query<br/>app/api/v1/routes/query.py]
    ingestRoute[Document APIs<br/>/api/v1/documents]
    evalRoute[POST /api/v1/evaluations/rag<br/>app/api/v1/routes/evaluations.py]
    historyRoute[History APIs<br/>/api/v1/history]

    subgraph QueryPath[Online RAG Query Path]
        auth[JWT Authentication<br/>tenant + role claims]
        tenant[Tenant Resolution<br/>server-side filters]
        guardIn[Input Guardrails<br/>app/guardrails/policy.py]
        memoryRead[Session Memory Read<br/>RedisMemoryStore]
        queryEmbed[Gemini Query Embedding<br/>task_type=RETRIEVAL_QUERY]
        dense[Dense Retrieval<br/>Qdrant]
        sparse[Sparse Retrieval<br/>Qdrant sparse vector]
        filters[Metadata Filters<br/>tenant / dept / role / tags]
        fusion[Qdrant RRF Fusion<br/>Query API]
        rerank[Cross-Encoder Reranker<br/>optional BGE / sentence-transformers]
        llm[Gemini Generation<br/>app/rag/llm.py]
        citations[Legal Citations<br/>source / page / chunk / score]
        guardOut[Output Guardrails]
        memoryWrite[Session Memory Write<br/>Redis]
        response[Answer + Sources + Trace ID]
    end

    subgraph IngestionPath[Async Legal Document Ingestion Path]
        upload[Legal Document Upload<br/>PDF / DOCX / TXT / MD / HTML / CSV]
        storage[(S3 / MinIO<br/>original files)]
        metadata[(MongoDB<br/>file metadata)]
        celery[Celery Queue<br/>Redis broker]
        worker[Ingestion Worker<br/>app/workers/tasks.py]
        parser[Document Parsing<br/>future loader layer]
        chunker[Configurable Chunking<br/>DOCUMENT_CHUNK_SIZE / OVERLAP]
        docEmbed[Gemini Document Embedding<br/>task_type=RETRIEVAL_DOCUMENT]
        lexical[Sparse Vector Generation<br/>app/rag/sparse.py]
        indexer[Document Indexer<br/>app/ingestion/indexer.py]
        qdrant[(Qdrant<br/>dense + sparse vectors)]
    end

    subgraph SharedPlatform[Platform Services]
        redis[(Redis<br/>memory / broker / results)]
        langfuse[Langfuse<br/>optional traces]
        otel[OpenTelemetry<br/>service traces]
        evals[Evaluation Hooks<br/>app/evaluation/rag.py]
        config[Environment Configuration<br/>app/core/config.py]
    end

    user --> api
    legalUser --> api
    api --> authRoute
    api --> queryRoute
    api --> ingestRoute
    api --> evalRoute
    api --> historyRoute

    authRoute --> auth
    queryRoute --> auth
    auth --> tenant
    tenant --> guardIn
    guardIn --> memoryRead
    memoryRead --> queryEmbed
    queryEmbed --> dense
    queryEmbed --> sparse
    filters --> dense
    filters --> sparse
    dense --> fusion
    sparse --> fusion
    fusion --> rerank
    rerank --> llm
    llm --> citations
    citations --> guardOut
    guardOut --> memoryWrite
    memoryWrite --> response
    response --> user
    response --> legalUser

    ingestRoute --> upload
    upload --> storage
    upload --> metadata
    upload --> celery
    celery --> worker
    worker --> parser
    parser --> chunker
    chunker --> docEmbed
    chunker --> lexical
    docEmbed --> indexer
    lexical --> indexer
    indexer --> qdrant

    qdrant -. serves .-> dense
    qdrant -. serves .-> sparse
    redis -. stores .-> memoryRead
    memoryWrite -. stores .-> redis
    celery -. uses .-> redis

    queryRoute -. traces .-> langfuse
    queryRoute -. traces .-> otel
    evalRoute --> evals
    config -. controls .-> chunker
    config -. controls .-> llm
    config -. controls .-> qdrant
```

## Runtime Flow

1. The client sends a query to FastAPI.
2. Auth resolves user, tenant, and role context. In the current scaffold, auth exists under `/api/v1/auth`; production tenant claims should be injected server-side before retrieval.
3. The RAG pipeline validates the query, loads Redis conversation memory, embeds the query with Gemini using `RETRIEVAL_QUERY`, builds a lexical sparse query vector, and runs Qdrant hybrid retrieval.
4. Metadata filters enforce tenant, department, role, tag, and legal-domain boundaries during retrieval.
5. Results are merged with reciprocal rank fusion, optionally reranked with a cross-encoder, then passed to Gemini for grounded answer generation.
6. Legal citation metadata is returned from source chunks where available: document ID, source, page, chunk index, and confidence score.
7. The response is guardrail-checked, written back to Redis session memory, traced, and returned with source chunks and a trace ID.
8. Legal document ingestion runs asynchronously through Celery: uploaded or JSON-provided documents are parsed, chunked with configurable chunk settings, embedded with Gemini using `RETRIEVAL_DOCUMENT`, converted to sparse lexical vectors, then indexed into Qdrant.

## Configurable Legal Profile

The legal document profile is controlled through [app/core/config.py](/Users/dev/Documents/resume-projects/productionRAG/app/core/config.py) and [.env.example](/Users/dev/Documents/resume-projects/productionRAG/.env.example):

| Variable | Purpose |
| --- | --- |
| `PLATFORM_PROFILE` | Runtime profile, default `enterprise` |
| `DOCUMENT_DOMAIN` | Domain profile, default `legal` |
| `DOCUMENT_CHUNK_SIZE` | Legal document chunk size used by Celery ingestion |
| `DOCUMENT_CHUNK_OVERLAP` | Chunk overlap used to preserve clause continuity |
| `LEGAL_CITATIONS_REQUIRED` | Signals that answers should preserve source citation metadata |
| `LEGAL_REQUIRED_METADATA_FIELDS` | Comma-separated metadata fields expected for legal retrieval boundaries |
