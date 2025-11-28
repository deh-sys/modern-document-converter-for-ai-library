"""
Title formatting module for law journal articles.
Formats titles for use in filenames.
"""

import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Words to remove from titles (articles, prepositions, etc.)
STOP_WORDS = {
    'a', 'an', 'the',           # Articles
    'and', 'or', 'but',          # Conjunctions
    'in', 'on', 'at', 'to',      # Common prepositions
    'of', 'for', 'with', 'from', # More prepositions
    'by', 'as',
}


class TitleFormatter:
    """Format article titles for use in filenames."""

    def __init__(self, max_words=6):
        """
        Initialize title formatter.

        Args:
            max_words: Maximum words to keep in formatted title (default: 6)
        """
        self.max_words = max_words

    def format_for_filename(self, title):
        """
        Format title for use in filename.
        Process: Remove stop words -> Remove special chars -> Limit words -> Join with underscores

        Args:
            title: Article title (e.g., "The Rise of Directed Verdict: Jury Power in Civil Cases")

        Returns:
            str: Formatted title (e.g., "Rise_Directed_Verdict_Jury_Power_Civil_Cases")
        """
        if not title:
            return "Unknown_Title"

        # Step 1: Remove subtitle (after colon) if it makes title too long
        main_title, subtitle = self._split_title_subtitle(title)

        # Try formatting with main title only first
        formatted = self._format_title_part(main_title)

        # If main title is short enough, add some subtitle words
        words = formatted.split('_')
        if len(words) < self.max_words and subtitle:
            subtitle_formatted = self._format_title_part(subtitle)
            subtitle_words = subtitle_formatted.split('_')

            # Add subtitle words up to max_words limit
            words_to_add = min(len(subtitle_words), self.max_words - len(words))
            if words_to_add > 0:
                words.extend(subtitle_words[:words_to_add])

        # Ensure we don't exceed max_words
        words = words[:self.max_words]

        # Join with underscores
        return '_'.join(words) if words else "Unknown_Title"

    def _split_title_subtitle(self, title):
        """
        Split title into main title and subtitle at colon.

        Returns:
            tuple: (main_title, subtitle or None)
        """
        if ':' in title:
            parts = title.split(':', 1)
            return parts[0].strip(), parts[1].strip()
        else:
            return title, None

    def _format_title_part(self, text):
        """
        Format a title part (main or subtitle).
        Remove stop words, special chars, etc.

        Returns:
            str: Formatted title with underscores
        """
        # Remove special characters (keep letters, numbers, spaces)
        text = re.sub(r'[^\w\s-]', '', text)

        # Split into words
        words = text.split()

        # Filter and process words
        significant_words = []

        for i, word in enumerate(words):
            word_lower = word.lower()

            # Keep first word even if it's a stop word
            if i == 0:
                significant_words.append(word)
                continue

            # Skip stop words (unless it's a meaningful part of a phrase)
            if word_lower in STOP_WORDS and len(word_lower) <= 3:
                continue

            # Skip very short words (1-2 letters) unless they're all caps
            if len(word) <= 2 and not word.isupper():
                continue

            significant_words.append(word)

        # Title case each word
        significant_words = [self._title_case_word(w) for w in significant_words]

        return '_'.join(significant_words)

    def _title_case_word(self, word):
        """
        Convert word to title case, handling special cases.

        Returns:
            str: Title cased word
        """
        # If word is all caps and longer than 1 letter, preserve it (e.g., "USA")
        if len(word) > 1 and word.isupper():
            return word

        # Otherwise, title case
        return word.capitalize()

    def shorten_title(self, title, max_length=50):
        """
        Alternative: Shorten title to character limit while preserving words.

        Args:
            title: Full title
            max_length: Maximum character length

        Returns:
            str: Shortened title
        """
        formatted = self.format_for_filename(title)

        if len(formatted) <= max_length:
            return formatted

        # Remove words from end until under limit
        words = formatted.split('_')
        while len('_'.join(words)) > max_length and len(words) > 2:
            words.pop()

        return '_'.join(words)
