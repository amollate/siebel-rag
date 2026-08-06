import logging
import os

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

    def add_documents(self, documents, ids=None):
        collection = self._get_collection()

        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        texts = [doc.get("text", "") for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]

        if not texts:
            logger.warning("No documents to add to vector store.")
            return

        embeddings = self._embedder.embed(texts)

        if isinstance(embeddings, np.ndarray):
            embeddings = embeddings.tolist()

        batch_size = 500
        for i in range(0, len(texts), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]

            collection.add(
                ids=batch_ids,
                documents=batch_texts,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
            )
            logger.info("Added batch %d-%d to vector store", i, i + len(batch_ids))

        logger.info("Total documents in store: %d", collection.count())

    def search(self, query, top_k=5, similarity_threshold=0.35):
        collection = self._get_collection()

        query_embedding = self._embedder.embed_single(query)

        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()

        if not query_embedding:
            return []

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

        logger.info("Search returned %d matches for query: '%s...'",
                     len(matches), query[:60])
        return matches

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
        logger.info("Reset vector store collection: %s", self.collection_name)