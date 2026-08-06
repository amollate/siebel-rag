import logging
import os

from ingestion.scraper import SiebelDocScraper
from ingestion.parser import SiebelDocParser
from ingestion.chunker import TextChunker
from embedding.embedder import Embedder
from vector_store.store import VectorStore
from retrieval.retriever import SiebelRetriever
from generation.generator import SiebelGenerator

from config import (
    SIEBEL_SOURCES, CHUNK_SIZE, CHUNK_OVERLAP,
    TOP_K_RETRIEVAL, SIMILARITY_THRESHOLD,
)

logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class SiebelRAGPipeline:
    def __init__(self):
        self.scraper = None
        self.parser = None
        self.chunker = None
        self.embedder = None
        self.vector_store = None
        self.retriever = None
        self.generator = None

    def _init_components(self):
        self.scraper = SiebelDocScraper(max_pages=30, delay=1.5)
        self.parser = SiebelDocParser()
        self.chunker = TextChunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        self.retriever = SiebelRetriever(
            vector_store=self.vector_store,
            top_k=TOP_K_RETRIEVAL,
            similarity_threshold=SIMILARITY_THRESHOLD,
        )
        self.generator = SiebelGenerator()

    def ingest(self, sources=None):
        if sources is None:
            sources = SIEBEL_SOURCES

        self._init_components()

        all_documents = []
        for source in sources:
            logger.info("=" * 60)
            logger.info("Ingesting source: %s", source["name"])
            logger.info("URL: %s", source["url"])

            self.scraper.base_url = source["url"]
            self.scraper.to_visit = [source["url"]]
            self.scraper.visited = set()
            self.scraper.collected = []

            crawled = self.scraper.crawl()
            all_documents.extend(crawled)

        logger.info("Total crawled pages: %d", len(all_documents))

        parsed = self.parser.parse(all_documents)
        logger.info("Total parsed sections: %d", len(parsed))

        chunks = []
        for doc in parsed:
            metadata = {
                "url": doc["url"],
                "source": doc["source"],
                "section_title": doc["section_title"],
            }
            doc_chunks = self.chunker.chunk(doc["content"], metadata=metadata)
            chunks.extend(doc_chunks)

        logger.info("Total chunks created: %d", len(chunks))

        self.vector_store.add_documents(chunks)
        logger.info("Ingestion complete. %d chunks in vector store.",
                     self.vector_store.count())

        return len(chunks)

    def query(self, question: str) -> dict:
        if self.retriever is None:
            self._init_components()

        logger.info("Processing query: '%s'", question)

        retrieved = self.retriever.retrieve_with_scores(question)

        if not retrieved:
            return {
                "query": question,
                "answer": "No relevant documents found in the knowledge base.",
                "sources": [],
                "retrieved_count": 0,
            }

        answer = self.generator.generate(question, retrieved)

        sources = []
        for doc in retrieved:
            sources.append({
                "source": doc.get("metadata", {}).get("source", "Unknown"),
                "section": doc.get("metadata", {}).get("section_title", ""),
                "url": doc.get("metadata", {}).get("url", ""),
                "similarity": round(doc.get("relevance_score", 0), 4),
            })

        return {
            "query": question,
            "answer": answer,
            "sources": sources,
            "retrieved_count": len(retrieved),
        }

    def interactive(self):
        print("\n" + "=" * 60)
        print("  Siebel 6 Knowledge Base — RAG Query Interface")
        print("=" * 60)
        print("\nType your questions about Siebel CRM (version 6).")
        print("Commands: 'quit' to exit, 'status' for info, 'reset' to re-index.\n")

        while True:
            try:
                user_input = input("\nSiebel RAG > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye.")
                break
            if user_input.lower() == "status":
                count = self.vector_store.count() if self.vector_store else 0
                print(f"  Vector store documents: {count}")
                print(f"  Embedding model: {self.embedder.model_name if self.embedder else 'N/A'}")
                print(f"  Top-K retrieval: {TOP_K_RETRIEVAL}")
                print(f"  Similarity threshold: {SIMILARITY_THRESHOLD}")
                continue
            if user_input.lower() == "reset":
                if self.vector_store:
                    self.vector_store.reset()
                print("  Vector store reset. Re-run ingestion to repopulate.")
                continue

            result = self.query(user_input)

            print(f"\n{'=' * 60}")
            print(f"  ANSWER")
            print(f"{'=' * 60}")
            print(result["answer"])

            if result["sources"]:
                print(f"\n{'=' * 60}")
                print(f"  SOURCES ({result['retrieved_count']} retrieved)")
                print(f"{'=' * 60}")
                for i, src in enumerate(result["sources"], 1):
                    print(f"  [{i}] {src['source']} — {src['section']}")
                    print(f"      Similarity: {src['similarity']:.4f}")
                    if src["url"]:
                        print(f"      URL: {src['url']}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Siebel 6 Knowledge Base RAG System"
    )
    parser.add_argument(
        "--ingest", action="store_true",
        help="Crawl and index Siebel documentation sources",
    )
    parser.add_argument(
        "--query", type=str, default=None,
        help="Ask a question about Siebel 6 knowledge",
    )
    parser.add_argument(
        "--interactive", action="store_true",
        help="Start interactive query mode",
    )

    args = parser.parse_args()

    pipeline = SiebelRAGPipeline()

    if args.ingest:
        pipeline.ingest()
    elif args.query:
        result = pipeline.query(args.query)
        print(f"\nQuery: {result['query']}")
        print(f"\nAnswer:\n{result['answer']}")
        if result["sources"]:
            print(f"\nSources:")
            for s in result["sources"]:
                print(f"  - {s['source']} ({s['section']}): {s['similarity']:.4f}")
    elif args.interactive:
        pipeline.interactive()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()