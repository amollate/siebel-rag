import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.retriever import SiebelRetriever


class MockVectorStore:
    def __init__(self, documents=None):
        self.documents = documents or []

    def search(self, query, top_k=5, similarity_threshold=0.35):
        results = []
        for i, doc in enumerate(self.documents):
            results.append({
                "text": doc.get("text", ""),
                "metadata": doc.get("metadata", {}),
                "similarity": doc.get("similarity", 0.5),
                "id": doc.get("id", f"doc_{i}"),
            })
        return results[:top_k]


class TestSiebelRetriever(unittest.TestCase):
    def setUp(self):
        self.mock_docs = [
            {"text": "Siebel CRM is an enterprise CRM platform.", "metadata": {"source": "Oracle"}, "similarity": 0.9, "id": "doc_0"},
            {"text": "Business Components are the data layer.", "metadata": {"source": "Oracle"}, "similarity": 0.7, "id": "doc_1"},
            {"text": "Applets display Business Component data.", "metadata": {"source": "Cleverence"}, "similarity": 0.5, "id": "doc_2"},
            {"text": "Views contain applets.", "metadata": {"source": "Oracle"}, "similarity": 0.3, "id": "doc_3"},
            {"text": "Workflows automate business processes.", "metadata": {"source": "Aired"}, "similarity": 0.1, "id": "doc_4"},
        ]
        self.store = MockVectorStore(self.mock_docs)
        self.retriever = SiebelRetriever(
            vector_store=self.store,
            top_k=3,
            similarity_threshold=0.35,
        )

    def test_retrieve_returns_top_k(self):
        results = self.retriever.retrieve("What is Siebel CRM?")
        self.assertLessEqual(len(results), 3)

    def test_retrieve_filters_by_threshold(self):
        results = self.retriever.retrieve("What is Siebel CRM?")
        for r in results:
            self.assertGreaterEqual(r["similarity"], 0.35)

    def test_retrieve_with_scores(self):
        results = self.retriever.retrieve_with_scores("What is Siebel CRM?")
        for r in results:
            self.assertIn("relevance_score", r)
        scores = [r["relevance_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_retrieve_empty_results(self):
        empty_store = MockVectorStore([])
        retriever = SiebelRetriever(vector_store=empty_store, top_k=3)
        results = retriever.retrieve("Some query")
        self.assertEqual(len(results), 0)

    def test_retrieve_multi_query(self):
        expansions = ["Siebel business components", "Siebel applets"]
        results = self.retriever.retrieve_multi_query(
            "What are Siebel components?",
            expansions=expansions,
        )
        self.assertLessEqual(len(results), 3)

    def test_retrieve_preserves_metadata(self):
        results = self.retriever.retrieve("What is Siebel CRM?")
        for r in results:
            self.assertIn("metadata", r)
            self.assertIn("source", r["metadata"])


if __name__ == "__main__":
    unittest.main()