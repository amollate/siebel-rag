import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class SiebelRetriever:
    def __init__(self, vector_store, top_k=5, similarity_threshold=0.35):
        self.vector_store = vector_store
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    def retrieve(self, query: str) -> List[Dict]:
        logger.info("Retrieving documents for query: '%s'", query)

        results = self.vector_store.search(
            query=query,
            top_k=self.top_k,
            similarity_threshold=self.similarity_threshold,
        )

        if not results:
            logger.warning("No relevant documents found for query: '%s'", query)

        return results

    def retrieve_with_scores(self, query: str) -> List[Dict]:
        results = self.retrieve(query)

        for r in results:
            score = r.get("similarity", 0.0)
            r["relevance_score"] = round(score, 4)

        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return results

    def retrieve_multi_query(self, query: str, expansions: List[str] = None) -> List[Dict]:
        all_results = []

        queries = [query]
        if expansions:
            queries.extend(expansions)

        for q in queries:
            results = self.retrieve(q)
            all_results.extend(results)

        seen = set()
        unique_results = []
        for r in all_results:
            doc_id = r.get("id", r.get("text", ""))[:100]
            if doc_id not in seen:
                seen.add(doc_id)
                unique_results.append(r)

        unique_results.sort(key=lambda x: x.get("relevance_score", x.get("similarity", 0)), reverse=True)

        return unique_results[:self.top_k]