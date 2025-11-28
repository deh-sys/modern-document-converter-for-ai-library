"""
Code Generator Service - Document Processor

Generate unique 5-letter codes for document identification with full legacy compatibility.

Architecture:
    - Base-25 encoding (A-Z excluding 'W')
    - 5-character codes: AAAAA through ZZZZZ (9,765,625 possible codes)
    - Discovery logic: Detects and preserves existing codes in filenames
    - Validation: Ensures codes meet strict format requirements

Legacy Compatibility:
    - Port of step2/filename_indexer.py algorithm
    - Compatible with existing 249,025+ allocated codes
    - Maintains "----CODE" separator convention
    - Validates against invalid characters (especially 'W')

Usage:
    from src.services.code_generator import CodeGenerator

    generator = CodeGenerator(registrar)
    code = generator.allocate_code_for_file(Path("document.pdf"))
    # Returns: "AAAAA" (new) or existing code from filename
"""

import re
from pathlib import Path
from typing import Optional

# ============================================================================
# CONSTANTS - Legacy Compatibility
# ============================================================================

# Alphabet: A-Z excluding 'W' (25 characters total)
# This gives 25^5 = 9,765,625 possible unique codes
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVXYZ"  # No 'W'

# Code format
CODE_LENGTH = 5
SEPARATOR = "----"

# Regex pattern to extract code from filename
# Matches: ----[A-VX-Z]{5} followed by extension or end of string
# Examples: "document----ABCDE.pdf", "folder----XYZAB"
CODE_PATTERN = re.compile(r"----([A-VX-Z]{5})(?:\.|$)")


# ============================================================================
# PURE FUNCTIONS - Core Algorithm
# ============================================================================

def index_to_code(idx: int) -> str:
    """
    Convert integer index to 5-letter code using base-25 encoding.

    Algorithm (ported from step2/filename_indexer.py):
        1. Take index (0, 1, 2, ..., 9,765,624)
        2. Convert to base-25 representation
        3. Map each digit to alphabet (A=0, B=1, ..., Z=24, skip W)
        4. Build 5-letter code from right to left
        5. Reverse to get proper order

    Args:
        idx: Integer index (0-9,765,624)

    Returns:
        5-letter code string (e.g., "AAAAA", "AAAAB", "BCDEZ")

    Raises:
        RuntimeError: If index exceeds maximum (registry exhausted)

    Examples:
        >>> index_to_code(0)
        'AAAAA'
        >>> index_to_code(1)
        'AAAAB'
        >>> index_to_code(24)
        'AAAAZ'
        >>> index_to_code(25)
        'AAABA'
    """
    base = len(ALPHABET)  # 25
    limit = base ** CODE_LENGTH  # 9,765,625

    if idx >= limit:
        raise RuntimeError(
            f"Registry exhausted: index {idx} exceeds maximum {limit - 1}. "
            f"No more unique codes available."
        )

    if idx < 0:
        raise ValueError(f"Index must be non-negative, got: {idx}")

    # Build digits from right to left (least significant to most significant)
    digits: list[str] = []
    for _ in range(CODE_LENGTH):
        digits.append(ALPHABET[idx % base])
        idx //= base

    # Reverse to get proper order (most significant digit first)
    return "".join(reversed(digits))


def code_to_index(code: str) -> int:
    """
    Convert 5-letter code back to integer index.

    Reverse operation of index_to_code(). Useful for validation and testing.

    Args:
        code: 5-letter code string (e.g., "AAAAA", "BCDEZ")

    Returns:
        Integer index (0-9,765,624)

    Raises:
        ValueError: If code format is invalid

    Examples:
        >>> code_to_index("AAAAA")
        0
        >>> code_to_index("AAAAB")
        1
        >>> code_to_index("AAABA")
        25
    """
    if not is_valid_code(code):
        raise ValueError(
            f"Invalid code format: {code}. "
            f"Must be {CODE_LENGTH} uppercase letters from A-Z excluding W."
        )

    base = len(ALPHABET)
    index = 0

    for char in code:
        index = index * base + ALPHABET.index(char)

    return index


def is_valid_code(code: str) -> bool:
    """
    Validate code format and character restrictions.

    Requirements:
        - Exactly 5 characters long
        - All uppercase letters
        - Only characters from A-Z excluding 'W'
        - No whitespace or special characters

    Args:
        code: String to validate

    Returns:
        True if code meets all requirements, False otherwise

    Examples:
        >>> is_valid_code("ABCDE")
        True
        >>> is_valid_code("ZZZZZ")
        True
        >>> is_valid_code("WWWWW")
        False  # Contains 'W'
        >>> is_valid_code("ABC")
        False  # Too short
        >>> is_valid_code("abcde")
        False  # Lowercase
    """
    if not code:
        return False

    if len(code) != CODE_LENGTH:
        return False

    if not code.isupper():
        return False

    # Check each character is in allowed alphabet (no 'W')
    for char in code:
        if char not in ALPHABET:
            return False

    return True


# ============================================================================
# FILENAME UTILITIES
# ============================================================================

def extract_code_from_filename(filename: str) -> Optional[str]:
    """
    Extract code from filename using regex pattern.

    Searches for pattern: ----[A-VX-Z]{5} (followed by extension or end)

    Args:
        filename: Filename to search (with or without path)

    Returns:
        Extracted code if found and valid, None otherwise

    Examples:
        >>> extract_code_from_filename("document----ABCDE.pdf")
        'ABCDE'
        >>> extract_code_from_filename("old_statute----XYZAB.docx")
        'XYZAB'
        >>> extract_code_from_filename("document----WWWWW.pdf")
        None  # Invalid code (contains W)
        >>> extract_code_from_filename("no_code.pdf")
        None  # No code present
    """
    # Get just the filename if full path provided
    name = Path(filename).name

    # Search for pattern
    match = CODE_PATTERN.search(name)
    if not match:
        return None

    code = match.group(1)

    # Validate extracted code
    if not is_valid_code(code):
        return None

    return code


def has_code_suffix(filename: str) -> bool:
    """
    Check if filename already has a valid code suffix.

    Args:
        filename: Filename to check

    Returns:
        True if valid code suffix found, False otherwise

    Examples:
        >>> has_code_suffix("document----ABCDE.pdf")
        True
        >>> has_code_suffix("document.pdf")
        False
        >>> has_code_suffix("document----WWWWW.pdf")
        False  # Invalid code
    """
    return extract_code_from_filename(filename) is not None


def append_code_to_filename(filename: str, code: str) -> str:
    """
    Add code suffix to filename before extension.

    Handles files with and without extensions.
    Preserves directory path if present.

    Args:
        filename: Original filename (e.g., "document.pdf")
        code: 5-letter code to append (e.g., "ABCDE")

    Returns:
        Filename with code suffix (e.g., "document----ABCDE.pdf")

    Raises:
        ValueError: If code is invalid

    Examples:
        >>> append_code_to_filename("document.pdf", "ABCDE")
        'document----ABCDE.pdf'
        >>> append_code_to_filename("folder", "XYZAB")
        'folder----XYZAB'
        >>> append_code_to_filename("/path/to/file.txt", "BCDEZ")
        '/path/to/file----BCDEZ.txt'
    """
    if not is_valid_code(code):
        raise ValueError(f"Invalid code: {code}")

    path = Path(filename)

    # Get stem (filename without extension) and suffix (extension with dot)
    stem = path.stem
    suffix = path.suffix

    # Build new filename: stem + ---- + code + extension
    new_name = f"{stem}{SEPARATOR}{code}{suffix}"

    # Preserve parent directory if present
    if path.parent != Path("."):
        return str(path.parent / new_name)

    return new_name


def strip_code_from_filename(filename: str) -> str:
    """
    Remove code suffix from filename if present.

    Args:
        filename: Filename possibly containing code

    Returns:
        Filename with code removed

    Examples:
        >>> strip_code_from_filename("document----ABCDE.pdf")
        'document.pdf'
        >>> strip_code_from_filename("document.pdf")
        'document.pdf'  # No change if no code
    """
    name = str(filename)

    # Remove code pattern if found
    name = CODE_PATTERN.sub("", name)

    return name


# ============================================================================
# CODE GENERATOR SERVICE
# ============================================================================

class CodeGenerator:
    """
    Code generation service with legacy compatibility and discovery logic.

    Features:
        - Base-25 encoding (A-Z excluding W)
        - Automatic code discovery from filenames
        - Validation and format enforcement
        - Integration with registrar for persistence

    Discovery Logic (Critical):
        When allocating code for a file:
        1. Check filename for existing code using regex
        2. If valid code found: Return it (preserve legacy codes)
        3. If no code or invalid: Generate new code

    Example:
        generator = CodeGenerator(registrar)

        # New file
        code = generator.allocate_code_for_file(Path("document.pdf"))
        # Returns: "AAAAA" (new code)

        # Legacy file
        code = generator.allocate_code_for_file(Path("old----XYZAB.pdf"))
        # Returns: "XYZAB" (existing code preserved)

        # Invalid code
        code = generator.allocate_code_for_file(Path("bad----WWWWW.pdf"))
        # Returns: "AAAAB" (invalid code replaced)
    """

    def __init__(self, registrar):
        """
        Initialize code generator with registrar service.

        Args:
            registrar: Registrar service instance for persistence
        """
        self.registrar = registrar

    def generate_next_code(self) -> str:
        """
        Generate next sequential code from registrar's index.

        Workflow:
            1. Get current code index from registrar
            2. Increment index atomically
            3. Convert index to code
            4. Allocate code in database
            5. Return code

        Returns:
            Next available 5-letter code

        Raises:
            RuntimeError: If code registry is exhausted
        """
        # Get and increment index atomically
        index = self.registrar.increment_code_index()

        # Convert to code
        code = index_to_code(index)

        # Allocate in database
        self.registrar.allocate_code(code)

        return code

    def allocate_code_for_file(self, file_path: Path) -> str:
        """
        Allocate code for file with automatic discovery logic.

        Discovery Logic:
            1. Extract filename from path
            2. Search for existing code with regex
            3. Validate found code
            4. If valid: Return existing code (Scenario A)
            5. If invalid/missing: Generate new code (Scenario B)

        Args:
            file_path: Path to file (may or may not contain code)

        Returns:
            Code to use (existing or newly generated)

        Examples:
            # Scenario A: Legacy file with valid code
            allocate_code_for_file(Path("statute----ABXCD.pdf"))
            # Returns: "ABXCD"

            # Scenario B: New file, no code
            allocate_code_for_file(Path("document.pdf"))
            # Returns: "AAAAA" (or next available)

            # Scenario B: Invalid code (contains W)
            allocate_code_for_file(Path("bad----WWWWW.pdf"))
            # Returns: "AAAAB" (new valid code)
        """
        filename = file_path.name

        # Try to extract existing code
        existing_code = extract_code_from_filename(filename)

        if existing_code:
            # Valid code found - preserve it (Scenario A)
            # Register code in database if not already present
            if not self.registrar.code_exists(existing_code):
                self.registrar.allocate_code(existing_code)

            return existing_code

        # No valid code found - generate new one (Scenario B)
        return self.generate_next_code()

    def rollback_code(self, code: str) -> None:
        """
        Return code to available pool after failed operation.

        Only works if code was most recently allocated and not committed.
        Delegates to registrar for actual rollback logic.

        Args:
            code: Code to rollback

        Example:
            code = generator.generate_next_code()
            try:
                rename_file(old_path, new_path_with_code)
            except Exception:
                generator.rollback_code(code)  # Return code to pool
        """
        self.registrar.rollback_code(code)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_code_range(start_index: int, count: int = 10) -> list[str]:
    """
    Generate a range of codes for display/testing.

    Args:
        start_index: Starting index
        count: Number of codes to generate

    Returns:
        List of codes

    Example:
        >>> format_code_range(0, 5)
        ['AAAAA', 'AAAAB', 'AAAAC', 'AAAAD', 'AAAAE']
    """
    codes = []
    for i in range(start_index, start_index + count):
        try:
            codes.append(index_to_code(i))
        except RuntimeError:
            break
    return codes


def get_code_statistics() -> dict:
    """
    Get statistics about code capacity and usage.

    Returns:
        Dict with capacity info

    Example:
        >>> stats = get_code_statistics()
        >>> print(stats)
        {
            'alphabet_size': 25,
            'code_length': 5,
            'total_capacity': 9765625,
            'alphabet': 'ABCDEFGHIJKLMNOPQRSTUVXYZ'
        }
    """
    return {
        "alphabet_size": len(ALPHABET),
        "code_length": CODE_LENGTH,
        "total_capacity": len(ALPHABET) ** CODE_LENGTH,
        "alphabet": ALPHABET,
    }
