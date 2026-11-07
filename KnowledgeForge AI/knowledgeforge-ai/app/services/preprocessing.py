"""Text cleaning and normalization pipeline for ingested documents."""

import re
import unicodedata
from typing import Optional


class TextPreprocessor:
    """Provides modular text normalization and cleaning routines."""

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Normalize Unicode characters to NFKC format."""
        if not text:
            return ""
        return unicodedata.normalize("NFKC", text)

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """Collapse redundant spaces while preserving meaningful paragraph breaks."""
        if not text:
            return ""
        # Replace non-breaking spaces and carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
        # Replace multiple spaces/tabs with single space on each line
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        # Collapse more than two consecutive newlines into double newlines
        cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
        return cleaned.strip()

    @staticmethod
    def strip_control_characters(text: str) -> str:
        """Remove unprintable ASCII/Unicode control characters except newline and tab."""
        if not text:
            return ""
        return "".join(
            ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\t")
        )

    @classmethod
    def preprocess(cls, text: str) -> str:
        """Run complete preprocessing sequence."""
        if not text:
            return ""
        cleaned = cls.strip_control_characters(text)
        cleaned = cls.normalize_unicode(cleaned)
        cleaned = cls.clean_whitespace(cleaned)
        return cleaned

