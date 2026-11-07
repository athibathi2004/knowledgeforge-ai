"""Intelligent chunking engine with recursive, fixed, and sliding window strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional
from app.services.parser import DocumentSegment, ParsedDocument


@dataclass
class Chunk:
    """Represents an extracted semantic text chunk with metadata."""

    content: str
    chunk_index: int
    token_count: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseChunker(ABC):
    """Abstract base class for chunking implementations."""

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 120):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count based on whitespace tokenization and subword heuristic."""
        if not text:
            return 0
        words = text.split()
        # English text averages ~1.3 tokens per word
        return max(1, int(len(words) * 1.3))

    @abstractmethod
    def split_text(self, text: str, initial_offset: int = 0) -> List[Chunk]:
        """Split raw text into chunks."""
        pass

    def chunk_document(self, parsed_doc: ParsedDocument) -> List[Chunk]:
        """Chunk a parsed document, preserving segment (page/section) metadata."""
        all_chunks: List[Chunk] = []
        global_chunk_idx = 0

        # If document has structural segments (e.g. pages or sections), chunk segment-by-segment
        if parsed_doc.segments:
            for segment in parsed_doc.segments:
                seg_chunks = self.split_text(segment.text, initial_offset=segment.char_offset)
                for chunk in seg_chunks:
                    chunk.chunk_index = global_chunk_idx
                    global_chunk_idx += 1
                    if segment.page_number is not None:
                        chunk.metadata["page_number"] = segment.page_number
                    if segment.section_header is not None:
                        chunk.metadata["section_header"] = segment.section_header
                    chunk.metadata["filename"] = parsed_doc.filename
                    chunk.metadata["file_type"] = parsed_doc.file_type
                    all_chunks.append(chunk)
        else:
            all_chunks = self.split_text(parsed_doc.full_text, initial_offset=0)
            for idx, chunk in enumerate(all_chunks):
                chunk.chunk_index = idx
                chunk.metadata["filename"] = parsed_doc.filename
                chunk.metadata["file_type"] = parsed_doc.file_type

        return all_chunks


class RecursiveCharacterChunker(BaseChunker):
    """Hierarchical text splitter using customizable separator hierarchy."""

    def __init__(
        self,
        chunk_size: int = 600,
        chunk_overlap: int = 120,
        separators: Optional[List[str]] = None,
    ):
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.separators = separators or ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    def _split_with_separators(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using the first separator that divides the content."""
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        if not separators:
            # Fallback to hard slice if no separators remain
            return [
                text[i : i + self.chunk_size]
                for i in range(0, len(text), self.chunk_size - self.chunk_overlap)
            ]

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            splits = list(text)
        elif separator in (". ", "? ", "! "):
            # Split with sentence boundary lookbehind
            splits = [s for s in re.split(f"(?<=[.?!]) +", text) if s]
        else:
            splits = [s for s in text.split(separator) if s]

        if len(splits) <= 1:
            return self._split_with_separators(text, remaining_separators)

        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for split in splits:
            split_len = len(split) + (len(separator) if separator != "" else 0)
            if current_length + split_len > self.chunk_size and current_chunk:
                merged = separator.join(current_chunk) if separator != "" else "".join(current_chunk)
                if len(merged) > self.chunk_size:
                    chunks.extend(self._split_with_separators(merged, remaining_separators))
                else:
                    chunks.append(merged)
                current_chunk = []
                current_length = 0

            current_chunk.append(split)
            current_length += split_len

        if current_chunk:
            merged = separator.join(current_chunk) if separator != "" else "".join(current_chunk)
            if len(merged) > self.chunk_size:
                chunks.extend(self._split_with_separators(merged, remaining_separators))
            else:
                chunks.append(merged)

        return chunks

    def split_text(self, text: str, initial_offset: int = 0) -> List[Chunk]:
        """Split text recursively and compute offsets and token counts."""
        raw_pieces = self._split_with_separators(text, self.separators)
        chunks: List[Chunk] = []
        cursor = initial_offset

        for idx, piece in enumerate(raw_pieces):
            piece_stripped = piece.strip()
            if not piece_stripped:
                continue

            start_char = text.find(piece_stripped, max(0, cursor - initial_offset))
            if start_char == -1:
                start_char = cursor
            else:
                start_char += initial_offset
            end_char = start_char + len(piece_stripped)
            cursor = end_char

            chunks.append(
                Chunk(
                    content=piece_stripped,
                    chunk_index=idx,
                    token_count=self.estimate_tokens(piece_stripped),
                    start_char=start_char,
                    end_char=end_char,
                )
            )

        return chunks


class FixedSizeChunker(BaseChunker):
    """Character-window based chunker with constant step size and overlap."""

    def split_text(self, text: str, initial_offset: int = 0) -> List[Chunk]:
        chunks: List[Chunk] = []
        text_len = len(text)
        if text_len == 0:
            return chunks

        step = max(1, self.chunk_size - self.chunk_overlap)
        idx = 0
        for i in range(0, text_len, step):
            window = text[i : i + self.chunk_size].strip()
            if not window:
                continue
            start_char = initial_offset + i
            end_char = start_char + len(window)
            chunks.append(
                Chunk(
                    content=window,
                    chunk_index=idx,
                    token_count=self.estimate_tokens(window),
                    start_char=start_char,
                    end_char=end_char,
                )
            )
            idx += 1
            if i + self.chunk_size >= text_len:
                break

        return chunks


class SlidingWindowChunker(BaseChunker):
    """Token/word-aware sliding window chunker."""

    def split_text(self, text: str, initial_offset: int = 0) -> List[Chunk]:
        words = text.split()
        if not words:
            return []

        # Convert char chunk size to estimated word count (~5 chars per word)
        target_words = max(10, self.chunk_size // 5)
        overlap_words = max(2, self.chunk_overlap // 5)
        step = max(1, target_words - overlap_words)

        chunks: List[Chunk] = []
        chunk_idx = 0

        for i in range(0, len(words), step):
            window_words = words[i : i + target_words]
            chunk_content = " ".join(window_words).strip()
            if not chunk_content:
                continue

            chunks.append(
                Chunk(
                    content=chunk_content,
                    chunk_index=chunk_idx,
                    token_count=self.estimate_tokens(chunk_content),
                    start_char=initial_offset,
                    end_char=initial_offset + len(chunk_content),
                )
            )
            chunk_idx += 1
            if i + target_words >= len(words):
                break

        return chunks


class ChunkerFactory:
    """Factory to instantiate chunking strategy by name."""

    _chunkers = {
        "recursive": RecursiveCharacterChunker,
        "fixed": FixedSizeChunker,
        "sliding_window": SlidingWindowChunker,
    }

    @classmethod
    def get_chunker(
        cls,
        strategy: str = "recursive",
        chunk_size: int = 600,
        chunk_overlap: int = 120,
    ) -> BaseChunker:
        chunker_cls = cls._chunkers.get(strategy.lower(), RecursiveCharacterChunker)
        return chunker_cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

