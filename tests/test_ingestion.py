import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.chunker import TextChunker


class TestTextChunker(unittest.TestCase):
    def setUp(self):
        self.chunker = TextChunker(chunk_size=10, chunk_overlap=2)

    def test_chunk_empty_text(self):
        result = self.chunker.chunk("")
        self.assertEqual(len(result), 0)

    def test_chunk_short_text(self):
        text = "This is a short text."
        result = self.chunker.chunk(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], text)

    def test_chunk_splits_long_text(self):
        sentences = [
            "This is sentence one.",
            "This is sentence two.",
            "This is sentence three.",
            "This is sentence four.",
            "This is sentence five.",
            "This is sentence six.",
            "This is sentence seven.",
            "This is sentence eight.",
        ]
        text = " ".join(sentences)
        result = self.chunker.chunk(text, metadata={"source": "test"})
        self.assertGreater(len(result), 1)

    def test_chunk_metadata_propagation(self):
        text = "This is a test sentence for metadata propagation."
        metadata = {"source": "test_source", "section_title": "Test Section"}
        result = self.chunker.chunk(text, metadata=metadata)
        for chunk in result:
            self.assertIn("metadata", chunk)
            self.assertEqual(chunk["metadata"]["source"], "test_source")
            self.assertEqual(chunk["metadata"]["section_title"], "Test Section")

    def test_chunk_overlap(self):
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        result = self.chunker.chunk(text, metadata={})
        for chunk in result:
            self.assertGreater(len(chunk["text"]), 0)

    def test_split_by_headers(self):
        text = (
            "INTRODUCTION\n"
            "This is the intro paragraph.\n\n"
            "ARCHITECTURE\n"
            "This describes the architecture.\n\n"
            "CONFIGURATION\n"
            "This covers configuration steps."
        )
        sections = self.chunker.split_by_headers(text)
        self.assertGreater(len(sections), 1)

    def test_split_by_sentence(self):
        text = "First sentence. Second sentence. Third sentence."
        sentences = self.chunker.split_by_sentence(text)
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0], "First sentence.")
        self.assertEqual(sentences[1], "Second sentence.")
        self.assertEqual(sentences[2], "Third sentence.")


if __name__ == "__main__":
    unittest.main()