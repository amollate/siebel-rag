# RAG Patterns Used in the Siebel 6 RAG Solution

This document catalogs the Retrieval-Augmented Generation (RAG) patterns implemented in this project, with references to the relevant code and design rationale.

---

## 1. Naive RAG (Basic Retrieve-and-Generate)

**Pattern**: The simplest RAG architecture — retrieve relevant documents, then pass them to an LLM as context for answer generation.

**Implementation**: `rag_pipeline.py` — the `query()` method calls `retriever.retrieve_with_scores()` then `generator.generate()`.

**When to use**: Single-hop questions where the answer is contained in one or a few documents.

**In this project**: Used as the baseline retrieval strategy. The user asks a question, the system retrieves the top-K most similar chunks, and the LLM generates an answer from those chunks.

**Code reference**:
- `retrieval/retriever.py:retrieve()` — basic retrieval
- `generation/generator.py:generate()` — context-augmented generation

---

## 2. Dense Retrieval with Semantic Embeddings

**Pattern**: Convert both documents and queries into dense vector embeddings using a transformer model, then perform approximate nearest-neighbor search.

**Implementation**: `embedding/embedder.py` uses `sentence-transformers/all-MiniLM-L6-v2`. `vector_store/store.py` uses ChromaDB's HNSW index with cosine distance.

**When to use**: When semantic meaning matters more than exact keyword matching. Effective for questions phrased differently from the source text.

**In this project**: This is the primary retrieval mechanism. The embedding model captures the semantic meaning of Siebel documentation sections, enabling queries like "How do I configure business components?" to match sections discussing Business Components even if the exact words differ.

**Code reference**:
- `embedding/embedder.py:embed()` — batch embedding
- `embedding/embedder.py:embed_single()` — single query embedding
- `vector_store/store.py:search()` — cosine similarity search

---

## 3. Metadata-Augmented Retrieval

**Pattern**: Store and filter on metadata alongside vector embeddings to narrow retrieval results.

**Implementation**: Each chunk in ChromaDB carries metadata: `url`, `source`, `section_title`. The vector store can filter by these fields.

**When to use**: When you need to restrict retrieval to specific sources, sections, or time periods.

**In this project**: Metadata includes the source name (e.g., "Oracle Official Documentation"), section title (e.g., "Architecture"), and URL. This enables:
- Filtering results to a specific documentation source
- Displaying source attribution in answers
- Debugging retrieval quality by examining which sections are retrieved

**Code reference**:
- `ingestion/chunker.py` — metadata propagation to chunks
- `vector_store/store.py:add_documents()` — metadata storage
- `generation/generator.py:_build_prompt()` — metadata display in prompt

---

## 4. Similarity Thresholding

**Pattern**: Filter retrieval results by a minimum similarity score to avoid returning irrelevant documents.

**Implementation**: `vector_store/store.py:search()` filters results where `similarity < similarity_threshold` (default 0.35).

**When to use**: When the knowledge base contains noise or irrelevant content that could degrade answer quality.

**In this project**: The threshold prevents the LLM from being distracted by loosely related documents. If no documents meet the threshold, the system returns a "no relevant documents found" message instead of a potentially hallucinated answer.

**Code reference**:
- `config.py:SIMILARITY_THRESHOLD = 0.35`
- `vector_store/store.py:search()` — threshold filtering

---

## 5. Relevance Scoring and Ranking

**Pattern**: Return documents ranked by relevance score, with scores exposed to the user for transparency.

**Implementation**: `retrieval/retriever.py:retrieve_with_scores()` computes `relevance_score = 1.0 - cosine_distance` and sorts results in descending order.

**When to use**: When answer quality depends on the quality of retrieved documents. Scoring helps users and developers assess whether the RAG system is working correctly.

**In this project**: Scores are displayed in the interactive CLI and included in the prompt context so the LLM knows which documents are most relevant. Scores also enable future evaluation with RAGAS metrics.

**Code reference**:
- `retrieval/retriever.py:retrieve_with_scores()` — scoring and sorting

---

## 6. Multi-Source Ingestion

**Pattern**: Aggregate content from multiple documentation sources into a single knowledge base.

**Implementation**: `config.py:SIEBEL_SOURCES` defines 8 sources. `rag_pipeline.py:ingest()` iterates over all sources, crawls each, and adds all chunks to a single ChromaDB collection.

**When to use**: When knowledge is spread across multiple authoritative sources that need to be searched together.

**In this project**: Siebel 6 knowledge comes from Oracle's official docs, third-party guides, tutorials, and deployment guides. Combining them gives the RAG system a comprehensive view of the domain.

**Code reference**:
- `config.py:SIEBEL_SOURCES` — source list
- `rag_pipeline.py:ingest()` — multi-source crawling

---

## 7. Header-Aware Chunking

**Pattern**: Split documents at structural boundaries (section headers) rather than at arbitrary positions.

**Implementation**: `ingestion/chunker.py:chunk()` first splits by detected headers (`split_by_headers()`), then splits by sentences within each section.

**When to use**: When documents have clear section structures and semantic coherence within sections.

**In this project**: Siebel documentation is organized into sections like "Architecture", "Configuration", "Business Components", etc. Header-aware chunking ensures each chunk corresponds to a logical topic, improving retrieval precision.

**Code reference**:
- `ingestion/chunker.py:split_by_headers()` — header detection
- `ingestion/chunker.py:chunk()` — chunking pipeline

---

## 8. Overlap Chunking

**Pattern**: Add overlap between consecutive chunks to prevent information loss at chunk boundaries.

**Implementation**: `ingestion/chunker.py` uses `CHUNK_OVERLAP = 64` words of overlap. When a chunk exceeds the size limit, the last N sentences of the previous chunk are carried forward.

**When to use**: When chunk boundaries might cut important information in half (e.g., a sentence that spans two chunks).

**In this project**: Overlap ensures that concepts that span section boundaries are fully captured in at least one chunk. This is especially important for Siebel documentation where configuration steps or code examples may cross section boundaries.

**Code reference**:
- `ingestion/chunker.py:chunk()` — overlap logic
- `ingestion/chunker.py:_get_overlap()` — overlap extraction

---

## 9. Multi-Query Retrieval (Planned)

**Pattern**: Expand a single user query into multiple sub-queries and merge results for broader coverage.

**Implementation**: `retrieval/retriever.py:retrieve_multi_query()` accepts a list of query expansions and merges results, deduplicating by document ID.

**When to use**: When user queries are ambiguous or could match different aspects of the knowledge base.

**In this project**: The infrastructure is in place but not yet activated by default. Future work could auto-generate query expansions using the LLM.

**Code reference**:
- `retrieval/retriever.py:retrieve_multi_query()` — multi-query retrieval

---

## 10. Source Attribution in Generation

**Pattern**: Include source metadata in the LLM prompt so the generated answer includes citations.

**Implementation**: `generation/generator.py:_build_prompt()` includes the source name, section title, and relevance score for each retrieved document in the prompt.

**When to use**: When users need to verify the answer or explore the source material further.

**In this project**: Every answer includes a "SOURCES" section listing the retrieved documents with their source, section, and similarity score. This is critical for enterprise RAG systems where answer correctness must be auditable.

**Code reference**:
- `generation/generator.py:_build_prompt()` — source attribution in prompt
- `rag_pipeline.py:query()` — source list in response

---

## Pattern Evolution Roadmap

The current implementation uses patterns 1-8 and 10. The following advanced patterns are planned for future iterations:

| Pattern | Status | Priority |
|---------|--------|----------|
| Hybrid Search (dense + BM25) | Planned | High |
| Re-ranking (cross-encoder) | Planned | High |
| Multi-hop RAG | Planned | Medium |
| RAGAS evaluation | Planned | Medium |
| Agentic RAG | Planned | Low |
| GraphRAG | Planned | Low |

---

## References

1. Lewis, P., et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020. https://arxiv.org/abs/2005.11401
2. IBM. "Retrieval Augmented Generation: Enhance LLMs with Factual Data." https://www.ibm.com/think/architectures/patterns/genai-rag
3. Precision AI Academy. "RAG Tutorial 2026." https://precisionaiacademy.com/blog/rag-tutorial-python-2026
4. is4.ai. "How to Implement RAG in 2025." https://is4.ai/blog/our-blog-1/how-to-implement-rag-retrieval-augmented-generation-tutorial-22