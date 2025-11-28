"""
Filename quality evaluator for article files.
Determines if existing filename is good (manual work) or bad (download garbage).
"""

import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Generic/garbage filename patterns
GARBAGE_PATTERNS = [
    r'^download',           # download.pdf, download(1).pdf
    r'^document',           # document.pdf
    r'^untitled',           # untitled.pdf
    r'^article',            # article.pdf
    r'^paper',              # paper.pdf
    r'^file',               # file.pdf
    r'^new',                # new document.pdf
    r'^ssrn[-_]',           # ssrn-12345.pdf
    r'^jstor[-_]',          # jstor-article.pdf
    r'^doi[-_]',            # doi-12345.pdf
    r'^westlaw[-_]',        # westlaw-document.pdf
    r'^lexis[-_]',          # lexis-12345.pdf
    r'^\d+$',               # Just numbers: 12345.pdf
    r'^[a-f0-9]{8,}',       # Hex strings (hash-like filenames)
]

# Bad indicators (subtract from score)
BAD_INDICATORS = [
    (r'\(\d+\)', -2),                    # (1), (2), (final) → -2 each
    (r'\s+\(\d+\)', -2),                 # " (1)" with space → -2
    (r'\.tmp', -3),                       # .tmp files → -3
    (r'^.{1,5}\.', -2),                  # Very short (1-5 chars) → -2
    (r'^.{150,}\.', -1),                 # Very long (150+ chars) → -1
    (r'\s{2,}', -1),                     # Multiple spaces → -1
    (r'[^\w\s\-_\.]', -1),               # Special chars (not word/space/dash/underscore/dot) → -1
]

# Good indicators (add to score)
GOOD_INDICATORS = [
    (r'[A-Z][a-z]{2,}', +1),             # Capitalized word (author name likely) → +1
    (r'\d{4}', +1),                      # 4-digit year → +1
    (r'[_\-]', +1),                      # Uses underscore or hyphen → +1
    (r'[A-Z][a-z]+(?:[_\s][A-Z][a-z]+){2,}', +1),  # 3+ capitalized words → +1
]


class FilenameEvaluator:
    """Evaluate quality of existing filenames."""

    def evaluate_quality(self, filename):
        """
        Evaluate quality of existing filename.

        Args:
            filename: Original filename (with extension)

        Returns:
            tuple: (quality_level: str, score: int, reasons: list)
                   quality_level: "HIGH", "MEDIUM", or "LOW"
                   score: numeric score
                   reasons: list of reasons for the score
        """
        # Remove extension for evaluation
        name_stem = re.sub(r'\.(pdf|docx?)$', '', filename, flags=re.IGNORECASE)

        score = 0
        reasons = []

        # Check for garbage patterns (automatic LOW)
        for pattern in GARBAGE_PATTERNS:
            if re.search(pattern, name_stem, re.IGNORECASE):
                reasons.append(f"Garbage pattern: {pattern}")
                return ("LOW", -5, reasons)

        # Evaluate bad indicators
        for pattern, penalty in BAD_INDICATORS:
            matches = re.findall(pattern, name_stem)
            if matches:
                count = len(matches)
                score += penalty * count
                reasons.append(f"Bad: {pattern} (×{count}, {penalty * count} points)")

        # Evaluate good indicators
        for pattern, bonus in GOOD_INDICATORS:
            if re.search(pattern, name_stem):
                score += bonus
                reasons.append(f"Good: {pattern} (+{bonus} points)")

        # Additional heuristics

        # Check word count (meaningful multi-word names are good)
        words = re.findall(r'[A-Z][a-z]+', name_stem)
        meaningful_words = [w for w in words if len(w) >= 3]
        if len(meaningful_words) >= 3:
            score += 1
            reasons.append(f"Good: {len(meaningful_words)} meaningful words (+1)")
        elif len(meaningful_words) <= 1:
            score -= 1
            reasons.append(f"Bad: Only {len(meaningful_words)} meaningful words (-1)")

        # Check length (too short or too long is bad)
        if len(name_stem) < 10:
            score -= 1
            reasons.append(f"Bad: Very short filename ({len(name_stem)} chars, -1)")
        elif 15 <= len(name_stem) <= 80:
            score += 1
            reasons.append(f"Good: Reasonable length ({len(name_stem)} chars, +1)")

        # Convert score to quality level
        if score >= 3:
            quality = "HIGH"
        elif score >= 1:
            quality = "MEDIUM"
        else:
            quality = "LOW"

        return (quality, score, reasons)

    def should_replace(self, extraction_confidence, filename_quality, force=False):
        """
        Determine if filename should be replaced based on decision matrix.

        Args:
            extraction_confidence: "HIGH", "MEDIUM", "LOW", or "UNKNOWN"
            filename_quality: "HIGH", "MEDIUM", or "LOW"
            force: If True, always replace (override safety)

        Returns:
            tuple: (should_replace: bool, reason: str)
        """
        if force:
            return (True, "Forced replacement (--force flag)")

        if extraction_confidence == "UNKNOWN":
            return (False, "Extraction failed")

        # Decision matrix
        matrix = {
            # (extraction_confidence, filename_quality): (replace, reason)
            ("HIGH", "HIGH"):    (True,  "Both high quality - extracted version likely better"),
            ("HIGH", "MEDIUM"):  (True,  "High confidence extraction"),
            ("HIGH", "LOW"):     (True,  "High confidence extraction, existing filename is garbage"),

            ("MEDIUM", "HIGH"):  (False, "Keeping good manual filename (extraction only MEDIUM confidence)"),
            ("MEDIUM", "MEDIUM"): (True,  "Probable improvement"),
            ("MEDIUM", "LOW"):   (True,  "Any improvement over garbage filename"),

            ("LOW", "HIGH"):     (False, "Keeping good manual filename (extraction only LOW confidence)"),
            ("LOW", "MEDIUM"):   (False, "Too risky to replace decent filename"),
            ("LOW", "LOW"):      (True,  "Existing filename is garbage, can't be worse"),
        }

        key = (extraction_confidence, filename_quality)
        if key in matrix:
            return matrix[key]
        else:
            # Default: don't replace if unsure
            return (False, f"Unknown combination: {extraction_confidence} extraction, {filename_quality} quality")
