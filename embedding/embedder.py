import logging
import os

import numpy as np

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self, model_name=None):
        self.model_name = model_name or "sentence-transformers/all-MiniLM-L6-v2"
        self._model = None
        self._dimension = None
        self._ollama_client = None
        self._ollama_model = None

    def _load_sentence_transformers(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info("Loaded sentence-transformers model: %s (dim=%d)",
                        self.model_name, self._dimension)
        except Exception as e:
            logger.error("Failed to load sentence-transformers model: %s", e)
            raise

    def _load_ollama(self):
        if self._ollama_client is not None:
            return True
        try:
            import ollama
            self._ollama_client = ollama
            self._ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2")
            logger.info("Using Ollama embedding model: %s", self._ollama_model)
            return True
        except ImportError:
            logger.warning("Ollama package not installed, using sentence-transformers")
            return False

    @property
    def dimension(self):
        self._load_sentence_transformers()
        if self._dimension is not None:
            return self._dimension
        return 384

    def embed(self, texts):
        if not texts:
            return np.array([])

        use_ollama = os.environ.get("USE_OLLAMA", "true").lower() == "true"

        if use_ollama and self._load_ollama():
            try:
                embeddings = []
                for text in texts:
                    response = self._ollama_client.embeddings(
                        model=self._ollama_model,
                        prompt=text,
                    )
                    embeddings.append(response["embedding"])
                return np.array(embeddings)
            except Exception as e:
                logger.warning("Ollama embedding failed: %s, falling back to sentence-transformers", e)

        self._load_sentence_transformers()
        embeddings = self._model.encode(texts, show_progress_bar=False)
        return np.array(embeddings)

    def embed_single(self, text):
        result = self.embed([text])
        if len(result) == 0:
            return np.array([])
        return result[0]