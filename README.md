# Siebel 6 Knowledge Base — RAG Solution

A Retrieval-Augmented Generation (RAG) system built on Siebel 6 CRM knowledge materials collected from the internet. The system crawls Siebel documentation, chunks and embeds the content into a vector store, and serves question-answering over the knowledge base.

## Project Structure

```
siebel-rag/
├── README.md                  # This file
├── config.py                  # Configuration (sources, models, paths)
├── rag_pipeline.py            # Main RAG pipeline orchestrator
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── data/
│   └── sources.json           # List of Siebel knowledge sources
├── ingestion/                 # Data ingestion pipeline
│   ├── __init__.py
│   ├── scraper.py             # Web crawler for Siebel docs
│   ├── parser.py              # Document parser with section detection
│   └── chunker.py             # Text chunking strategy
├── embedding/                 # Embedding layer
│   ├── __init__.py
│   └── embedder.py            # Embedding model (sentence-transformers / Ollama)
├── vector_store/              # Vector database
│   ├── __init__.py
│   └── store.py               # ChromaDB vector store
├── retrieval/                 # Retrieval engine
│   ├── __init__.py
│   └── retriever.py           # Hybrid retrieval with scoring
├── generation/                # LLM generation layer
│   ├── __init__.py
│   └── generator.py           # Prompt construction + LLM call
├── docs/
│   ├── architecture.md        # Architecture design document
│   ├── step-by-step-guide.md  # Implementation walkthrough
│   └── rag-patterns.md        # RAG patterns used in this project
└── tests/                     # Test suite
    ├── __init__.py
    ├── test_ingestion.py
    ├── test_retrieval.py
    └── test_pipeline.py
```

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ingest Siebel documentation:
   ```bash
   python main.py --ingest
   ```

3. Ask a question:
   ```bash
   python main.py --query "What is the Siebel architecture?"
   ```

4. Interactive mode:
   ```bash
   python main.py --interactive
   ```

## Configuration

Edit `config.py` to adjust:
- **SIEBEL_SOURCES**: List of documentation URLs to crawl
- **CHUNK_SIZE / CHUNK_OVERLAP**: Text splitting parameters
- **TOP_K_RETRIEVAL**: Number of documents retrieved per query
- **SIMILARITY_THRESHOLD**: Minimum relevance score for results
- **USE_OLLAMA**: Set to `false` to use OpenAI embeddings instead

## Architecture

The RAG pipeline follows a standard four-stage architecture:

1. **Ingestion** — Crawl Siebel documentation, parse into sections, chunk into passages
2. **Embedding** — Convert each chunk into a dense vector using sentence-transformers
3. **Storage** — Store vectors in ChromaDB with metadata (source, section, URL)
4. **Retrieval + Generation** — At query time, embed the question, retrieve top-K chunks, and pass them to an LLM for grounded answer generation

See `docs/architecture.md` for the full design document.

## RAG Patterns

This project implements:
- **Naive RAG** — Basic retrieve-then-generate pipeline
- **Hybrid Search** — Cosine similarity on dense embeddings
- **Metadata Filtering** — Source and section-based filtering
- **Multi-Query Retrieval** — Expand queries for broader coverage

See `docs/rag-patterns.md` for details.

## License

This project is for educational and research purposes. All Siebel documentation content remains the property of Oracle Corporation.