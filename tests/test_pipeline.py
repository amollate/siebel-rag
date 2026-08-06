import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SIEBEL_SOURCES, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RETRIEVAL, SIMILARITY_THRESHOLD


class TestConfig(unittest.TestCase):
    def test_siebel_sources_not_empty(self):
        self.assertGreater(len(SIEBEL_SOURCES), 0)

    def test_siebel_sources_have_required_fields(self):
        for source in SIEBEL_SOURCES:
            self.assertIn("name", source)
            self.assertIn("url", source)
            self.assertIn("description", source)

    def test_siebel_source_urls_valid(self):
        from urllib.parse import urlparse
        for source in SIEBEL_SOURCES:
            parsed = urlparse(source["url"])
            self.assertIn(parsed.scheme, ("http", "https"))
            self.assertTrue(parsed.netloc)

    def test_chunk_size_positive(self):
        self.assertGreater(CHUNK_SIZE, 0)

    def test_chunk_overlap_non_negative(self):
        self.assertGreaterEqual(CHUNK_OVERLAP, 0)

    def test_chunk_overlap_less_than_chunk_size(self):
        self.assertLess(CHUNK_OVERLAP, CHUNK_SIZE)

    def test_top_k_positive(self):
        self.assertGreater(TOP_K_RETRIEVAL, 0)

    def test_similarity_threshold_in_range(self):
        self.assertGreaterEqual(SIMILARITY_THRESHOLD, 0.0)
        self.assertLessEqual(SIMILARITY_THRESHOLD, 1.0)


class TestPipelineImport(unittest.TestCase):
    def test_import_pipeline(self):
        try:
            from rag_pipeline import SiebelRAGPipeline
        except ImportError:
            self.skipTest("chromadb or other dependency not installed")
        pipeline = SiebelRAGPipeline()
        self.assertIsNotNone(pipeline)

    def test_import_components(self):
        from ingestion.scraper import SiebelDocScraper
        from ingestion.parser import SiebelDocParser
        from ingestion.chunker import TextChunker
        from embedding.embedder import Embedder
        try:
            from vector_store.store import VectorStore
            has_chromadb = True
        except ImportError:
            has_chromadb = False
        from retrieval.retriever import SiebelRetriever
        from generation.generator import SiebelGenerator

        scraper = SiebelDocScraper(base_url="https://example.com", max_pages=1)
        parser = SiebelDocParser()
        chunker = TextChunker(chunk_size=100, chunk_overlap=10)
        embedder = Embedder()
        generator = SiebelGenerator()

        self.assertIsNotNone(scraper)
        self.assertIsNotNone(parser)
        self.assertIsNotNone(chunker)
        self.assertIsNotNone(embedder)
        self.assertIsNotNone(generator)
        if has_chromadb:
            store = VectorStore()
            retriever = SiebelRetriever(vector_store=store, top_k=3)
            self.assertIsNotNone(store)
            self.assertIsNotNone(retriever)


if __name__ == "__main__":
    unittest.main()