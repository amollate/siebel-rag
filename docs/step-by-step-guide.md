# Siebel 6 RAG — Step-by-Step Implementation Guide

This document walks through each step of building the Siebel 6 RAG solution, explaining **what** was done and **why** at every stage.

---

## Step 1: Research Siebel 6 Knowledge Materials

**What**: Searched the internet for Siebel 6 CRM documentation, tutorials, architecture guides, configuration references, and deployment guides.

**Why**: A RAG system is only as good as its knowledge base. Before building anything, we need to identify authoritative sources of Siebel 6 knowledge. The research surfaced:

- **Oracle's official Siebel Bookshelf** — the primary documentation source
- **Cleverence's Siebel Fundamentals Guide** — comprehensive architecture and configuration coverage
- **ACTE's Siebel CRM Tutorial** — beginner-friendly overview of concepts
- **Aired's Siebel Tutorials Collection** — configuration articles and best practices
- **Oracle's Architecture Overview** — deployment planning and infrastructure details
- **A10 Networks Deployment Guide** — real-world deployment topology and configuration
- **SlideShare training materials** — structured learning content

**Result**: 8 curated sources identified and saved in `data/sources.json`.

---

## Step 2: Design the RAG Architecture

**What**: Designed a four-stage RAG architecture (Ingestion → Embedding → Storage → Retrieval + Generation) and documented it in `docs/architecture.md`.

**Why**: Before writing code, a clear architecture ensures all components fit together and the design is sound. The architecture was designed around these principles:

1. **Modularity** — each stage is an independent component that can be swapped or upgraded
2. **Offline-first** — uses open-source tools (sentence-transformers, ChromaDB, Ollama) so the system works without API keys
3. **Progressive enhancement** — starts with a working naive RAG and can be upgraded to hybrid search, re-ranking, or agentic RAG
4. **Traceability** — every answer includes source citations so users can verify information

**Result**: Architecture design document at `docs/architecture.md`.

---

## Step 3: Create Project Directory Structure

**What**: Created the following directory structure:

```
siebel-rag/
├── config.py
├── rag_pipeline.py
├── main.py
├── requirements.txt
├── data/
│   └── sources.json
├── ingestion/
│   ├── __init__.py
│   ├── scraper.py
│   ├── parser.py
│   └── chunker.py
├── embedding/
│   ├── __init__.py
│   └── embedder.py
├── vector_store/
│   ├── __init__.py
│   └── store.py
├── retrieval/
│   ├── __init__.py
│   └── retriever.py
├── generation/
│   ├── __init__.py
│   └── generator.py
├── docs/
│   ├── architecture.md
│   ├── step-by-step-guide.md
│   └── rag-patterns.md
└── tests/
    ├── __init__.py
    ├── test_ingestion.py
    ├── test_retrieval.py
    └── test_pipeline.py
```

**Why**: A clean, organized structure separates concerns and makes the codebase maintainable. Each module has a single responsibility:

- `ingestion/` — data collection and preparation
- `embedding/` — vector generation
- `vector_store/` — persistence and search
- `retrieval/` — relevance ranking
- `generation/` — answer synthesis

**Result**: Empty project skeleton with all directories and `__init__.py` files.

---

## Step 4: Implement the Ingestion Layer

**What**: Created three files in `ingestion/`:

### 4a. `scraper.py` — SiebelDocScraper

**What**: A BFS web crawler that starts from a seed URL, fetches pages, extracts text content, finds relevant links, and continues crawling.

**Why**: Siebel documentation is spread across multiple pages on Oracle's site and third-party blogs. A crawler automates the collection process. Key design choices:

- **BFS traversal** — ensures broad coverage before going deep
- **Relevance filtering** — only follows links containing Siebel/CRM-related keywords, avoiding noise
- **Rate limiting** (1.5s delay) — respects servers and avoids being blocked
- **HTML stripping** — removes scripts, styles, navigation, and footer elements to extract clean text

### 4b. `parser.py` — SiebelDocParser

**What**: Parses raw HTML text into structured sections by detecting section headers.

**Why**: Siebel documentation is organized into logical sections (Architecture, Configuration, Business Components, etc.). Splitting by sections preserves semantic boundaries and improves retrieval quality. The parser also extracts metadata (source name, domain, content length) for traceability.

### 4c. `chunker.py` — TextChunker

**What**: Splits document sections into overlapping chunks of configurable size (default 512 words).

**Why**: Embedding models have token limits. Long documents must be split into smaller passages. Key design choices:

- **Header-aware splitting** — first tries to split by section headers, preserving document structure
- **Sentence-level splitting** — ensures chunks don't break mid-sentence
- **Overlap** (default 64 words) — prevents information loss at chunk boundaries
- **Metadata propagation** — each chunk carries its source URL, section title, and source name

**Result**: Complete ingestion pipeline that can crawl, parse, and chunk Siebel documentation.

---

## Step 5: Implement the Embedding Layer

**What**: Created `embedding/embedder.py` — the `Embedder` class.

**Why**: Embeddings convert text into dense vectors that capture semantic meaning. This is the foundation of semantic search in RAG. Key design choices:

- **Model**: `sentence-transformers/all-MiniLM-L6-v2` — 384 dimensions, fast, accurate for semantic search
- **Dual backend**: Supports both sentence-transformers (offline) and Ollama (local LLM-based embeddings)
- **Batch processing** — embeds multiple texts efficiently
- **Dimension caching** — stores embedding dimension to avoid redundant computation

**Why MiniLM-L6-v2**: It's the most popular embedding model for RAG applications. At 384 dimensions, it's 4x smaller than `all-mpnet-base-v2` but retains ~95% of its retrieval quality. This makes it ideal for a local prototype.

**Result**: Working embedding component that can convert text to vectors.

---

## Step 6: Implement the Vector Store Layer

**What**: Created `vector_store/store.py` — the `VectorStore` class backed by ChromaDB.

**Why**: Vector databases store embeddings and enable fast similarity search. ChromaDB was chosen because:

1. **Embedded** — runs in-process, no external server needed
2. **Persistent** — data survives process restarts (stored on disk)
3. **Metadata support** — stores source, section title, and URL alongside vectors
4. **LangChain compatible** — can be swapped for other backends easily

Key design choices:

- **Cosine distance** — measures angular similarity between vectors, robust to document length
- **HNSW index** — approximate nearest-neighbor search, fast with high recall
- **Batch insertion** — adds documents in batches of 500 for efficiency
- **Similarity threshold** — filters out irrelevant results below a minimum score

**Result**: Working vector store that can add documents and perform similarity search.

---

## Step 7: Implement the Retrieval Layer

**What**: Created `retrieval/retriever.py` — the `SiebelRetriever` class.

**Why**: The retrieval layer bridges the vector store and the LLM. It takes a user query, finds relevant documents, and returns them ranked by relevance. Key design choices:

- **Relevance scoring** — returns cosine similarity scores so users can assess answer quality
- **Top-K parameterization** — configurable number of retrieved documents
- **Similarity threshold** — filters out low-quality matches
- **Multi-query retrieval** — expands queries with related terms for broader coverage

**Why scoring matters**: In RAG systems, transparency about which documents were used builds trust. Showing similarity scores lets users judge whether the answer is well-grounded.

**Result**: Working retrieval component with scoring and filtering.

---

## Step 8: Implement the Generation Layer

**What**: Created `generation/generator.py` — the `SiebelGenerator` class.

**Why**: The generation layer produces the final answer by combining the user's query with retrieved documents. Key design choices:

- **Three LLM backends** — Ollama (local), OpenAI (API), and a text fallback (no LLM needed)
- **Structured prompt** — system prompt instructs the LLM to act as a Siebel expert and answer ONLY from context
- **Source attribution** — each retrieved document is included with its source, section, and relevance score
- **Temperature control** (0.3) — low temperature for factual, deterministic answers

**Why the prompt structure matters**: The most common RAG failure mode is hallucination — the LLM generates plausible-sounding but incorrect answers. By explicitly instructing the LLM to use only the provided context, we dramatically reduce hallucination. Including source metadata lets users verify the answer.

**Result**: Working generation component that produces grounded answers with citations.

---

## Step 9: Build the Pipeline Orchestrator

**What**: Created `rag_pipeline.py` — the `SiebelRAGPipeline` class that orchestrates all components.

**Why**: The pipeline class provides a clean API for the two main operations:

1. **`ingest()`** — runs the full ingestion pipeline (scrape → parse → chunk → embed → store)
2. **`query()`** — runs retrieval + generation for a single question
3. **`interactive()`** — provides a CLI chat interface for repeated queries

The pipeline lazy-initializes components, so calling `query()` before `ingest()` will initialize all components on demand.

**Result**: A single entry point that ties all components together.

---

## Step 10: Create the CLI Entry Point

**What**: Created `main.py` with argparse-based CLI supporting three modes:

- `--ingest` — crawl and index all Siebel sources
- `--query "question"` — ask a single question and print the answer
- `--interactive` — start an interactive chat session

**Why**: A CLI interface makes the system easy to use, test, and integrate into scripts. It also serves as a quick way to verify the pipeline works without building a web UI.

**Result**: Functional CLI at `main.py`.

---

## Step 11: Write Tests

**What**: Created test files in `tests/` for ingestion, retrieval, and pipeline components.

**Why**: Tests ensure each component works correctly and catch regressions when modifying code. The tests cover:

- Chunking behavior (boundary cases, overlap, metadata propagation)
- Retrieval scoring and ranking
- Pipeline initialization and component wiring

**Result**: Test suite that validates core functionality.

---

## Step 12: Document the RAG Patterns

**What**: Created `docs/rag-patterns.md` documenting the RAG patterns implemented in this project.

**Why**: Documenting the patterns used helps future developers understand the design rationale and enables the team to evolve the system toward more advanced patterns (hybrid search, re-ranking, agentic RAG).

**Result**: Pattern documentation at `docs/rag-patterns.md`.

---

## Summary

| Step | Component | Key Decision |
|------|-----------|-------------|
| 1 | Research | 8 Siebel sources identified |
| 2 | Architecture | 4-stage modular RAG design |
| 3 | Project structure | Clean separation of concerns |
| 4 | Ingestion | BFS crawler + header-aware chunking |
| 5 | Embedding | sentence-transformers/all-MiniLM-L6-v2 |
| 6 | Vector Store | ChromaDB with cosine similarity |
| 7 | Retrieval | Top-K with similarity threshold + scoring |
| 8 | Generation | Prompt-engineered LLM with source attribution |
| 9 | Pipeline | Orchestrator with lazy initialization |
| 10 | CLI | argparse with ingest/query/interactive modes |
| 11 | Tests | Unit tests for core components |
| 12 | Documentation | Architecture, guide, and patterns |