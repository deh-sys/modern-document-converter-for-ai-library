"""
Document Classifier Service - Document Processor

YAML-driven document type classification using pattern matching and scoring.

Architecture:
    - Loads classification rules from config/document_types/*.yaml
    - Each document type has patterns with weights
    - Scores document against all types
    - Returns highest scoring type with confidence level

Usage:
    from src.services.classifier import classify

    result = classify(document_text)
    print(f"Type: {result.document_type}, Confidence: {result.confidence}")

Configuration:
    - Rules in: config/document_types/
    - caselaw.yaml - Legal cases (enabled)
    - statute.yaml - Statutes (disabled, placeholder)
    - article.yaml - Journal articles (disabled, placeholder)
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from src.core.models import Classification, DocumentType, ConfidenceLevel


# ============================================================================
# MODULE-LEVEL CACHE
# ============================================================================

# Cache loaded classification rules (loaded once at import)
_CLASSIFICATION_RULES: Optional[Dict[str, dict]] = None


# ============================================================================
# CONFIGURATION LOADING
# ============================================================================

def _load_classification_rules() -> Dict[str, dict]:
    """
    Load all classification rule files from config/document_types/.

    Returns:
        Dict mapping document type name to its rules.
        Only includes enabled rule files.

    Example:
        {
          'caselaw': {
            'document_type': 'caselaw',
            'patterns': [...],
            'confidence_thresholds': {...}
          }
        }

    Notes:
        - Caches results in module-level variable
        - Only loads files with 'enabled: true' or no 'enabled' field
        - Validates YAML structure
    """
    rules_dir = Path("config/document_types")

    if not rules_dir.exists():
        raise FileNotFoundError(
            f"Classification rules directory not found: {rules_dir}. "
            f"Expected config/document_types/*.yaml files."
        )

    loaded_rules = {}

    # Load all .yaml files
    for yaml_file in rules_dir.glob("*.yaml"):
        try:
            with yaml_file.open("r") as f:
                rules = yaml.safe_load(f)

            # Check if explicitly disabled
            if rules.get("enabled") is False:
                continue

            # Validate required fields
            doc_type = rules.get("document_type")
            if not doc_type:
                print(f"Warning: {yaml_file.name} missing 'document_type' field, skipping")
                continue

            if "patterns" not in rules or not rules["patterns"]:
                print(f"Warning: {yaml_file.name} has no patterns, skipping")
                continue

            loaded_rules[doc_type] = rules

        except yaml.YAMLError as e:
            print(f"Warning: Failed to load {yaml_file.name}: {e}")
            continue

    if not loaded_rules:
        raise ValueError(
            "No enabled classification rules found. "
            "Check config/document_types/*.yaml files."
        )

    return loaded_rules


def get_classification_rules() -> Dict[str, dict]:
    """
    Get classification rules (cached).

    Returns cached rules if available, otherwise loads from YAML files.

    Returns:
        Dict of classification rules by document type
    """
    global _CLASSIFICATION_RULES

    if _CLASSIFICATION_RULES is None:
        _CLASSIFICATION_RULES = _load_classification_rules()

    return _CLASSIFICATION_RULES


# ============================================================================
# PATTERN MATCHING & SCORING
# ============================================================================

def _match_pattern(text: str, pattern: dict) -> bool:
    """
    Check if pattern matches text.

    Args:
        text: Document text to search
        pattern: Pattern dict with 'pattern' and optional 'case_sensitive'

    Returns:
        True if pattern matches, False otherwise

    Example:
        pattern = {'pattern': r'\bv\.\s+\w+', 'case_sensitive': False}
        _match_pattern("Smith v. Jones", pattern)  # True
    """
    regex = pattern["pattern"]
    case_sensitive = pattern.get("case_sensitive", False)

    flags = 0 if case_sensitive else re.IGNORECASE

    try:
        return bool(re.search(regex, text, flags=flags))
    except re.error as e:
        print(f"Warning: Invalid regex pattern '{regex}': {e}")
        return False


def _score_document_type(text: str, rules: dict) -> Tuple[float, List[str]]:
    """
    Score document against a single document type's rules.

    Args:
        text: Document text
        rules: Classification rules for one document type

    Returns:
        Tuple of (score, matched_indicators)
        - score: Sum of matched pattern weights (0-100+)
        - matched_indicators: List of pattern descriptions that matched

    Example:
        score, indicators = _score_document_type(text, caselaw_rules)
        # score = 75.0
        # indicators = ["Case caption with 'v.'", "Court name", "Reporter citation"]
    """
    score = 0.0
    matched_indicators = []

    patterns = rules.get("patterns", [])

    for pattern in patterns:
        if _match_pattern(text, pattern):
            weight = pattern.get("weight", 0)
            score += weight

            # Track what matched (for debugging/explanation)
            description = pattern.get("description", pattern["pattern"])
            matched_indicators.append(description)

    return score, matched_indicators


def _score_to_confidence(score: float, thresholds: dict) -> ConfidenceLevel:
    """
    Map numeric score to confidence level.

    Args:
        score: Numeric score (0-100+)
        thresholds: Dict with 'high', 'medium', 'low' threshold values

    Returns:
        ConfidenceLevel enum (HIGH/MEDIUM/LOW)

    Example:
        thresholds = {'high': 60, 'medium': 30, 'low': 10}
        _score_to_confidence(75, thresholds)  # ConfidenceLevel.HIGH
        _score_to_confidence(40, thresholds)  # ConfidenceLevel.MEDIUM
        _score_to_confidence(15, thresholds)  # ConfidenceLevel.LOW
    """
    high_threshold = thresholds.get("high", 60)
    medium_threshold = thresholds.get("medium", 30)
    low_threshold = thresholds.get("low", 10)

    if score >= high_threshold:
        return ConfidenceLevel.HIGH
    elif score >= medium_threshold:
        return ConfidenceLevel.MEDIUM
    elif score >= low_threshold:
        return ConfidenceLevel.LOW
    else:
        # Score too low to be confident
        return None


# ============================================================================
# PUBLIC API
# ============================================================================

def classify(text: str, min_confidence: Optional[ConfidenceLevel] = None) -> Classification:
    """
    Classify document type based on text content.

    Uses YAML-defined patterns to score document against all known types.
    Returns highest scoring type with confidence level.

    Args:
        text: Extracted document text
        min_confidence: Optional minimum confidence level required
                       If result is below this, returns UNKNOWN

    Returns:
        Classification model with:
            - document_type: Best matching DocumentType
            - confidence: Numeric confidence (0.0-1.0)
            - indicators: List of matched pattern descriptions

    Example:
        classification = classify(document_text)
        if classification.document_type == DocumentType.CASELAW:
            print(f"Case detected with {classification.confidence:.0%} confidence")
            print(f"Matched patterns: {classification.indicators}")

    Algorithm:
        1. Load all enabled classification rules
        2. Score text against each document type
        3. Select highest scoring type
        4. Map score to confidence level (HIGH/MEDIUM/LOW)
        5. If confidence too low, return UNKNOWN
        6. Return Classification with type, confidence, and matched patterns
    """
    if not text or not text.strip():
        # Empty text -> unknown
        return Classification(
            document_type=DocumentType.UNKNOWN,
            confidence=0.0,
            indicators=["No text to classify"],
        )

    # Load classification rules
    rules_dict = get_classification_rules()

    # Score against all document types
    scores: Dict[str, Tuple[float, List[str]]] = {}

    for doc_type_name, rules in rules_dict.items():
        score, indicators = _score_document_type(text, rules)
        scores[doc_type_name] = (score, indicators)

    # Find highest scoring type
    best_type_name = None
    best_score = 0.0
    best_indicators = []

    for doc_type_name, (score, indicators) in scores.items():
        if score > best_score:
            best_score = score
            best_type_name = doc_type_name
            best_indicators = indicators

    # No matches found
    if best_type_name is None or best_score == 0:
        return Classification(
            document_type=DocumentType.UNKNOWN,
            confidence=0.0,
            indicators=["No patterns matched"],
        )

    # Get confidence thresholds for this type
    thresholds = rules_dict[best_type_name].get("confidence_thresholds", {})
    confidence_level = _score_to_confidence(best_score, thresholds)

    # Score too low for any confidence level
    if confidence_level is None:
        return Classification(
            document_type=DocumentType.UNKNOWN,
            confidence=min(best_score / 100.0, 1.0),  # Normalize to 0-1, cap at 1.0
            indicators=best_indicators + [f"Score {best_score} below minimum threshold"],
        )

    # Check minimum confidence requirement
    if min_confidence is not None:
        confidence_order = [ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH]
        if confidence_order.index(confidence_level) < confidence_order.index(min_confidence):
            return Classification(
                document_type=DocumentType.UNKNOWN,
                confidence=min(best_score / 100.0, 1.0),  # Normalize to 0-1, cap at 1.0
                indicators=best_indicators + [
                    f"Confidence {confidence_level.value} below required {min_confidence.value}"
                ],
            )

    # Map document type name to enum
    try:
        document_type = DocumentType(best_type_name)
    except ValueError:
        # Type name not in enum (shouldn't happen with valid YAML)
        print(f"Warning: Document type '{best_type_name}' not in DocumentType enum")
        document_type = DocumentType.UNKNOWN

    # Return successful classification
    # Cap confidence at 1.0 (scores can exceed 100 if many patterns match)
    return Classification(
        document_type=document_type,
        confidence=min(best_score / 100.0, 1.0),  # Normalize to 0-1, cap at 1.0
        indicators=best_indicators,
    )


def get_all_scores(text: str) -> Dict[str, Tuple[float, List[str]]]:
    """
    Get scores for all document types (for debugging/analysis).

    Args:
        text: Document text

    Returns:
        Dict mapping document type name to (score, indicators)

    Example:
        scores = get_all_scores(document_text)
        for doc_type, (score, indicators) in scores.items():
            print(f"{doc_type}: {score} points")
            for indicator in indicators:
                print(f"  - {indicator}")
    """
    if not text or not text.strip():
        return {}

    rules_dict = get_classification_rules()
    scores = {}

    for doc_type_name, rules in rules_dict.items():
        score, indicators = _score_document_type(text, rules)
        scores[doc_type_name] = (score, indicators)

    return scores


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def reload_rules():
    """
    Reload classification rules from YAML files.

    Useful for development/testing when rules are modified.
    Normally rules are cached at module import.

    Example:
        # Edit config/document_types/caselaw.yaml
        reload_rules()
        # New rules now active
    """
    global _CLASSIFICATION_RULES
    _CLASSIFICATION_RULES = _load_classification_rules()


def list_available_types() -> List[str]:
    """
    Get list of available (enabled) document types.

    Returns:
        List of document type names

    Example:
        types = list_available_types()
        print(f"Configured types: {', '.join(types)}")
    """
    rules_dict = get_classification_rules()
    return list(rules_dict.keys())
