# Siebel 6 RAG Solution — Architecture Design Document

## 1. Overview

This document describes the architecture of the Siebel 6 Knowledge Base RAG (Retrieval-Augmented Generation) system. The system enables users to ask natural-language questions about Siebel CRM version 6 and receive accurate, grounded answers derived from publicly available Siebel documentation.

## 2. Problem Statement

Siebel CRM (version 6, released circa 2003) is a mature enterprise CRM platform with extensive documentation spread across Oracle's documentation portal, third-party tutorials, deployment guides, and community resources. Finding specific information requires navigating multiple sources. A RAG system solves this by:

- **Centralizing** Siebel 6 knowledge from diverse sources
- **Indexing** content for semantic search
- **Grounding** LLM responses in retrieved documentation to reduce hallucination

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│  (CLI: python main.py --query / --interactive)                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   RAG PIPELINE (rag_pipeline.py)                │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  INGESTION    │───▶│  EMBEDDING   │───▶│  VECTOR STORE    │  │
│  │  (Scraper +   │    │  (Embedder)  │    │  (ChromaDB)      │  │
│  │   Parser +    │    │              │    │                  │  │
│  │   Chunker)    │    │              │    │                  │  │
│  └──────────────┘    └──────────────┘    └────────┬─────────┘  │
│                                                     │            │
│  ┌──────────────┐    ┌──────────────┐             │            │
│  │  RETRIEVAL    │◀───│  QUERY       │◀────────────┘            │
│  │  (Retriever)  │    │  PROCESSING  │                          │
│  └──────┬───────┘    └──────────────┘                          │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                              │
│  │  GENERATION   │                                              │
│  │  (Generator)  │                                              │
│  └──────┬───────┘                                              │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                              │
│  │  RESPONSE     │                                              │
│  │  + SOURCES    │                                              │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

## 4. Component Design

### 4.1 Ingestion Layer

**Purpose**: Collect Siebel documentation from the internet and prepare it for indexing.

**Components**:
- **SiebelDocScraper** (`ingestion/scraper.py`): Crawls Siebel documentation URLs using BFS with domain relevance filtering. Uses `requests` + `BeautifulSoup` for HTML extraction. Respects crawl delays and avoids revisiting pages.
- **SiebelDocParser** (`ingestion/parser.py`): Parses raw HTML text into structured sections by detecting section headers (e.g., "Architecture", "Configuration", "Business Components"). Extracts metadata including source name, domain, and section title.
- **TextChunker** (`ingestion/chunker.py`): Splits document sections into overlapping chunks of configurable size (default 512 words). Uses header-aware splitting followed by sentence-level chunking with overlap to maintain context continuity.

**Why this design**: Siebel documentation is long-form and structured. Header-aware chunking preserves semantic boundaries better than fixed-size splitting. Overlap prevents information loss at chunk boundaries.

### 4.2 Embedding Layer

**Purpose**: Convert text chunks into dense numerical vectors that capture semantic meaning.

**Component**: `Embedder` (`embedding/embedder.py`)

**Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) — a lightweight, fast model suitable for semantic search.

**Fallback**: Supports Ollama for local embedding generation if configured.

**Why this model**: MiniLM-L6-v2 provides an excellent balance between speed and accuracy for semantic search tasks. At 384 dimensions, it is memory-efficient while retaining good retrieval quality.

### 4.3 Vector Store Layer

**Purpose**: Store and efficiently retrieve vector embeddings with metadata.

**Component**: `VectorStore` (`vector_store/store.py`)

**Database**: ChromaDB — an open-source, embedded vector database that requires no external server. Stores vectors with associated metadata (source, section title, URL).

**Index**: HNSW (Hierarchical Navigable Small World) with cosine distance — optimized for approximate nearest-neighbor search with high recall.

**Why ChromaDB**: Zero-configuration, persists to disk, integrates natively with LangChain, and is ideal for a local RAG prototype. For production scale, it can be swapped for Pinecone, Weaviate, or Qdrant.

### 4.4 Retrieval Layer

**Purpose**: Retrieve the most relevant document chunks for a given user query.

**Component**: `SiebelRetriever` (`retrieval/retriever.py`)

**Strategy**: 
1. Embed the user query using the same embedding model
2. Perform cosine similarity search in ChromaDB
3. Filter results by similarity threshold (default 0.35)
4. Return top-K results sorted by relevance score

**Advanced patterns**:
- **Multi-query retrieval**: Expands the query with related terms and merges results
- **Relevance scoring**: Returns similarity scores for transparency

**Why cosine similarity**: It measures the angle between vectors, making it robust to document length variations and effective for semantic similarity.

### 4.5 Generation Layer

**Purpose**: Produce a grounded, factual answer by combining the retrieved context with the user's query.

**Component**: `SiebelGenerator` (`generation/generator.py`)

**LLM Backends** (in priority order):
1. **Ollama** (local, free) — uses `llama3.2` by default
2. **OpenAI** (API-based) — uses `gpt-4o-mini` with API key
3. **Fallback** — returns retrieved context excerpts with a note

**Prompt Design**: The system prompt instructs the LLM to act as a Siebel CRM expert and answer ONLY from the provided context. Each retrieved document is included with its source, section title, and relevance score for traceability.

**Why this prompt structure**: Explicit instructions to limit answers to the provided context reduce hallucination. Including source metadata enables users to verify answers.

## 5. Data Flow

### Indexing Phase (One-time)

```
URL List → Scraper → Raw HTML → Parser → Sections → Chunker → Chunks
    → Embedder → Vectors → ChromaDB (stored with metadata)
```

### Query Phase (Per-request)

```
User Query → Embedder → Query Vector → ChromaDB Search → Top-K Chunks
    → Generator (LLM + Context) → Answer + Source Citations
```

## 6. Configuration

All configurable parameters are in `config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CHUNK_SIZE` | 512 words | Maximum words per chunk |
| `CHUNK_OVERLAP` | 64 words | Overlap between consecutive chunks |
| `TOP_K_RETRIEVAL` | 5 | Number of documents retrieved per query |
| `SIMILARITY_THRESHOLD` | 0.35 | Minimum cosine similarity for results |
| `EMBEDDING_MODEL_NAME` | sentence-transformers/all-MiniLM-L6-v2 | Embedding model |
| `USE_OLLAMA` | true | Use Ollama for embedding/generation |
| `OLLAMA_MODEL` | llama3.2 | Ollama model for generation |

## 7. Design Decisions and Trade-offs

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| ChromaDB over Pinecone/Weaviate | Zero infrastructure, embedded, free | Not suitable for multi-node production |
| sentence-transformers over OpenAI embeddings | No API cost, works offline | Slightly lower quality than OpenAI embeddings |
| Header-aware chunking over fixed-size | Preserves semantic boundaries | May produce uneven chunk sizes |
| Cosine similarity over BM25 | Captures semantic meaning | Misses exact keyword matches (hybrid search can address this) |
| Single-vector retrieval over hybrid | Simpler implementation | Could be enhanced with BM25 fusion |

## 8. Future Enhancements

1. **Hybrid Search**: Add BM25 sparse retrieval and fuse with dense retrieval (Reciprocal Rank Fusion)
2. **Re-ranking**: Add a cross-encoder re-ranker (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`) for improved result ordering
3. **Multi-hop RAG**: For complex questions requiring multiple retrieval steps
4. **Evaluation**: Integrate RAGAS framework for automated quality metrics (faithfulness, relevance, answer correctness)
5. **Web UI**: Add a Streamlit or Gradio interface for non-technical users
6. **Incremental Indexing**: Support adding new sources without full re-indexing