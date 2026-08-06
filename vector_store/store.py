import logging
import os
import re

import chromadb
import numpy as np

from embedding.embedder import Embedder

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, persist_dir=None, collection_name="siebel_knowledge"):
        self.persist_dir = persist_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._embedder = Embedder()
        self._semantic_available = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        self._client = chromadb.PersistentClient(path=self.persist_dir)
        logger.info("Initialized ChromaDB persistent client at %s", self.persist_dir)
        return self._client

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        client = self._get_client()
        try:
            self._collection = client.get_collection(name=self.collection_name)
        except Exception:
            self._collection = client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("Created new collection: %s", self.collection_name)
        return self._collection

    def _check_semantic_available(self):
        if self._semantic_available is not None:
            return self._semantic_available
        try:
            test_emb = self._embedder.embed(["test"])
            self._semantic_available = len(test_emb) > 0 and not np.any(np.isnan(test_emb))
        except Exception:
            self._semantic_available = False
        return self._semantic_available

    def add_documents(self, documents, ids=None):
        collection = self._get_collection()
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        texts = [doc.get("text", "") for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        if not texts:
            logger.warning("No documents to add to vector store.")
            return
        if self._check_semantic_available():
            embeddings = self._embedder.embed(texts)
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
        else:
            embeddings = None
        batch_size = 500
        for i in range(0, len(texts), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size] if embeddings else None
            batch_metadatas = metadatas[i:i + batch_size]
            collection.add(
                ids=batch_ids,
                documents=batch_texts,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
            )
        logger.info("Total documents in store: %d", collection.count())

    def _keyword_search(self, query, top_k=5):
        collection = self._get_collection()
        all_docs = collection.get(include=["documents", "metadatas", "ids"])
        if not all_docs or not all_docs.get("documents"):
            return []
        query_lower = query.lower()
        query_terms = set(re.findall(r'\w+', query_lower))
        scored = []
        for i, doc in enumerate(all_docs["documents"]):
            doc_lower = doc.lower()
            doc_terms = set(re.findall(r'\w+', doc_lower))
            overlap = query_terms & doc_terms
            if not overlap:
                continue
            score = len(overlap) / max(len(query_terms), 1)
            metadatas = all_docs.get("metadatas", [])
            metadata = metadatas[i] if metadatas else {}
            scored.append({
                "text": doc,
                "metadata": metadata,
                "similarity": score,
                "id": all_docs["ids"][i] if all_docs.get("ids") else "",
            })
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]

    def search(self, query, top_k=5, similarity_threshold=0.35):
        collection = self._get_collection()
        if collection.count() == 0:
            logger.warning("Vector store is empty for query: '%s'", query[:60])
            return []
        if self._check_semantic_available():
            try:
                query_embedding = self._embedder.embed_single(query)
                if isinstance(query_embedding, np.ndarray):
                    query_embedding = query_embedding.tolist()
                if query_embedding:
                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=top_k,
                    )
                    matches = []
                    if results and results.get("documents"):
                        for i, doc in enumerate(results["documents"][0]):
                            distance = results["distances"][0][i] if results.get("distances") else 0
                            similarity = 1.0 - distance
                            if similarity >= similarity_threshold:
                                matches.append({
                                    "text": doc,
                                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                                    "similarity": similarity,
                                    "id": results["ids"][0][i] if results.get("ids") else "",
                                })
                    if matches:
                        logger.info("Semantic search returned %d matches", len(matches))
                        return matches
            except Exception as e:
                logger.warning("Semantic search failed: %s, falling back to keyword search", e)
        return self._keyword_search(query, top_k)

    def count(self):
        collection = self._get_collection()
        return collection.count()

    def reset(self):
        client = self._get_client()
        try:
            client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        self._collection = None
        self._collection = self._get_collection()
        self._semantic_available = None
        logger.info("Reset vector store collection: %s", self.collection_name)