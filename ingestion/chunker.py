import logging
import re

logger = logging.getLogger(__name__)


class TextChunker:
    def __init__(self, chunk_size=512, chunk_overlap=64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_by_headers(self, text):
        sections = re.split(r'(?:^|\n)(?=[A-Z][A-Z\s]{4,}\n)', text)
        sections = [s.strip() for s in sections if s.strip()]
        if len(sections) > 1:
            return sections
        return [text]

    def split_by_sentence(self, text):
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk(self, text, metadata=None):
        sections = self.split_by_headers(text)
        chunks = []
        current_chunk = []
        current_length = 0

        for section in sections:
            sentences = self.split_by_sentence(section)

            for sentence in sentences:
                sentence_len = len(sentence.split())

                if current_length + sentence_len > self.chunk_size and current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append({
                        "text": chunk_text,
                        "word_count": current_length,
                        "metadata": metadata or {},
                    })

                    overlap_sentences = self._get_overlap(current_chunk)
                    current_chunk = overlap_sentences
                    current_length = sum(len(s.split()) for s in current_chunk)

                current_chunk.append(sentence)
                current_length += sentence_len

        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "word_count": current_length,
                "metadata": metadata or {},
            })

        logger.info("Split text into %d chunks (size=%d, overlap=%d).",
                     len(chunks), self.chunk_size, self.chunk_overlap)
        return chunks

    def _get_overlap(self, chunk, num_sentences=3):
        if len(chunk) <= num_sentences:
            return chunk[:]
        return chunk[-num_sentences:]