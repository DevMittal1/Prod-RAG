# End-to-End Architecture

For the full system guide, see [end-to-end.md](/Users/dev/Documents/resume-projects/productionRAG/docs/end-to-end.md).

```mermaid
flowchart TB
    user[Client / App User]
    api[FastAPI API<br/>app/main.py]
    queryRoute[POST /api/v1/query<br/>app/api/v1/routes/query.py]
    ingestRoute[POST /api/v1/documents<br/>app/api/v1/routes/documents.py]
    evalRoute[POST /api/v1/evaluations/rag<br/>app/api/v1/routes/evaluations.py]

    subgraph QueryPath[Online RAG Query Path]
        guardIn[Input Guardrails<br/>app/guardrails/policy.py]
        memoryRead[Session Memory Read<br/>RedisMemoryStore]
        queryEmbed[Gemini Query Embedding<br/>task_type=RETRIEVAL_QUERY]
        dense[Dense Retrieval<br/>Qdrant]
        sparse[Sparse Retrieval<br/>Qdrant sparse vector]
        filters[Metadata Filters<br/>tenant / dept / role / tags]
        fusion[Qdrant RRF Fusion<br/>Query API]
        rerank[Cross-Encoder Reranker<br/>optional BGE / sentence-transformers]
        llm[Gemini Generation<br/>app/rag/llm.py]
        guardOut[Output Guardrails]
        memoryWrite[Session Memory Write<br/>Redis]
        response[Answer + Sources + Trace ID]
    end

    subgraph IngestionPath[Async Document Ingestion Path]
        celery[Celery Queue<br/>Redis broker]
        worker[Ingestion Worker<br/>app/workers/tasks.py]
        chunker[Chunk Documents<br/>app/ingestion/chunking.py]
        docEmbed[Gemini Document Embedding<br/>task_type=RETRIEVAL_DOCUMENT]
        indexer[Document Indexer<br/>app/ingestion/indexer.py]
        qdrant[(Qdrant<br/>dense + sparse vectors)]
    end

    subgraph SharedPlatform[Platform Services]
        redis[(Redis<br/>memory / broker / results)]
        langfuse[Langfuse<br/>optional traces]
        otel[OpenTelemetry<br/>service traces]
        evals[Evaluation Hooks<br/>app/evaluation/rag.py]
    end

    user --> api
    api --> queryRoute
    api --> ingestRoute
    api --> evalRoute

    queryRoute --> guardIn
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
    llm --> guardOut
    guardOut --> memoryWrite
    memoryWrite --> response
    response --> user

    ingestRoute --> celery
    celery --> worker
    worker --> chunker
    chunker --> docEmbed
    docEmbed --> indexer
    indexer --> qdrant

    qdrant -. serves .-> dense
    qdrant -. serves .-> sparse
    redis -. stores .-> memoryRead
    memoryWrite -. stores .-> redis
    celery -. uses .-> redis

    queryRoute -. traces .-> langfuse
    queryRoute -. traces .-> otel
    evalRoute --> evals
```

## Runtime Flow

1. The client sends a query to FastAPI.
2. The RAG pipeline validates the query, loads Redis conversation memory, embeds the query with Gemini using `RETRIEVAL_QUERY`, builds a lexical sparse query vector, and runs Qdrant hybrid retrieval.
3. Metadata filters enforce tenant, department, role, and tag boundaries during retrieval.
4. Results are merged with reciprocal rank fusion, optionally reranked with a cross-encoder, then passed to Gemini for grounded answer generation.
5. The response is guardrail-checked, written back to Redis session memory, traced, and returned with source chunks.
6. Document ingestion runs asynchronously through Celery: documents are chunked, embedded with Gemini using `RETRIEVAL_DOCUMENT`, converted to sparse lexical vectors, then indexed into Qdrant.
