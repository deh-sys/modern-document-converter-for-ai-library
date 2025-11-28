"""
Regex-only cleaner for historical OCR TXT files.

This script preserves page markers/OCR status markers while removing running
headers/footers, marking headings, repairing line breaks and hyphenation, and
adding a small metadata header. No AI or external APIs are used.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List, Sequence


PAGE_MARKER_PATTERN = re.compile(r"^---\[.*PDF Page.*\]---$")
OCR_FAILED_PATTERN = re.compile(r"^\[OCR FAILED:")
RUNNING_HEADER_CANDIDATE = re.compile(r"^[A-Z0-9 ,.'-]{4,60}$")
BARE_PAGE_NUMBER = re.compile(r"^\d{1,4}$")
BARE_ROMAN_NUMERAL = re.compile(r"^[ivxlcdmIVXLCDM]{1,6}$")
HEADING_ALL_CAPS = re.compile(r"^[A-Z0-9 ,.'-]+$")
HEADING_NUMBERED = re.compile(r"^(?:[IVXLCDM]+\.\s+.+|\d+\.\s+.+)$")

TYPO_REPLACEMENTS = [
    (r"ſ", "s"),
    (r"ﬁ", "fi"),
    (r"ﬂ", "fl"),
    (r"æ", "ae"),
    (r"Æ", "Ae"),
    (r"[“”]", '"'),
    (r"[‘’]", "'"),
    (r"—", " — "),
    (r"–", "-"),
    (r"•", ", "),
    (r"[àáâäå]", "a"),
    (r"[ÀÁÂÄÅ]", "A"),
    (r"[èéêë]", "e"),
    (r"[ÈÉÊË]", "E"),
    (r"[ìíîï]", "i"),
    (r"[ÌÍÎÏ]", "I"),
    (r"[òóôö]", "o"),
    (r"[ÒÓÔÖ]", "O"),
    (r"[ùúûü]", "u"),
    (r"[ÙÚÛÜ]", "U"),
    (r"ç", "c"),
    (r"Ç", "C"),
    (r"ñ", "n"),
    (r"Ñ", "N"),
]

OCR_REPLACEMENTS = [
    (r"\btbe\b", "the"),
    (r"\btbis\b", "this"),
    (r"\btbat\b", "that"),
    (r"\bfub\b", "sub"),
    (r"\binft\b", "inst"),
    (r"\bmodem\b", "modern"),
    (r"\bcomer\b", "corner"),
]

MODERN_SPELLINGS = [
    (r"\bpublick\b", "public"),
    (r"\bCatholick\b", "Catholic"),
    (r"\bcatholick\b", "catholic"),
    (r"\bpolitick\b", "politic"),
    (r"\bpoliticks\b", "politics"),
    (r"\bpractick\b", "practic"),
    (r"\bpracticks\b", "practics"),
    (r"\bmusick\b", "music"),
    (r"\bmusicalk?\b", "musical"),
    (r"\bphysick\b", "physic"),
    (r"\bphysicks\b", "physics"),
    (r"\bauthentick\b", "authentic"),
    (r"\bauthentically\b", "authentically"),
    (r"\bhonour\b", "honor"),
    (r"\bhonours\b", "honors"),
    (r"\bhonourable\b", "honorable"),
    (r"\bcolour\b", "color"),
    (r"\bcolours\b", "colors"),
    (r"\bneighbour\b", "neighbor"),
    (r"\bneighbours\b", "neighbors"),
    (r"\blabour\b", "labor"),
    (r"\blabours\b", "labors"),
    (r"\bfavour\b", "favor"),
    (r"\bfavours\b", "favors"),
    (r"\bsaviour\b", "savior"),
    (r"\bbehaviour\b", "behavior"),
    (r"\bendeavour\b", "endeavor"),
    (r"\bvapour\b", "vapor"),
    (r"\bcentre\b", "center"),
    (r"\bcentres\b", "centers"),
    (r"\btheatre\b", "theater"),
    (r"\btheatres\b", "theaters"),
    (r"\bmetre\b", "meter"),
    (r"\bmetres\b", "meters"),
    (r"\bshew\b", "show"),
    (r"\bshewed\b", "showed"),
    (r"\bshewing\b", "showing"),
    (r"\bchuse\b", "choose"),
    (r"\bchuses\b", "chooses"),
    (r"\bchusing\b", "choosing"),
    (r"\bchused\b", "chose"),
    (r"\bsurprize\b", "surprise"),
    (r"\bsurprized\b", "surprised"),
    (r"\bsurprizing\b", "surprising"),
    (r"\bpublique\b", "public"),
    (r"\bpublicque\b", "public"),
    (r"\bantient\b", "ancient"),
    (r"\bancestours\b", "ancestors"),
    (r"\bintire\b", "entire"),
    (r"\bintirely\b", "entirely"),
    (r"\bcompleat\b", "complete"),
    (r"\bcompleatly\b", "completely"),
    (r"\bcompleated\b", "completed"),
    (r"\bcloaths?\b", "clothes"),
    (r"\bcloath\b", "cloth"),
    (r"\bcloathing\b", "clothing"),
    (r"\bmagick\b", "magic"),
    (r"\btragick\b", "tragic"),
    (r"\bcomedick\b", "comic"),
    (r"\bvpon\b", "upon"),
    (r"\bvnto\b", "unto"),
    (r"\bvnder\b", "under"),
    (r"\bvnited\b", "united"),
    (r"\bvnion\b", "union"),
    (r"\bvnjust\b", "unjust"),
    (r"\bvnless\b", "unless"),
    (r"\bvniuersal\b", "universal"),
    (r"\bvniuersity\b", "university"),
    (r"\bhaue\b", "have"),
    (r"\bsaue\b", "save"),
    (r"\bgiu(e|en|eth|ing)\b", r"giv\1"),
    (r"\beuer\b", "ever"),
    (r"\bneuer\b", "never"),
    (r"\bouer\b", "over"),
    (r"\bdoe\b", "do"),
    (r"\bdoeth\b", "does"),
    (r"\bdoth\b", "does"),
    (r"\bhath\b", "has"),
    (r"\bhadst\b", "had"),
    (r"\bshalt\b", "shall"),
    (r"\bshouldst\b", "should"),
    (r"\bwouldst\b", "would"),
    (r"\bcouldst\b", "could"),
    (r"\bmightst\b", "might"),
    (r"\bjudgement\b", "judgment"),
    (r"\bjudgements\b", "judgments"),
    (r"\backnowledgement\b", "acknowledgment"),
    (r"\backnowledgements\b", "acknowledgments"),
    (r"\bencrease\b", "increase"),
    (r"\benuy\b", "envy"),
    (r"\bantagonistick\b", "antagonistic"),
    (r"\bgaol\b", "jail"),
    (r"\bgaoler\b", "jailer"),
    (r"\binteftate\b", "intestate"),
    (r"\bestate\b", "estate"),
    (r"\bcommoditie?s\b", "commodities"),
    (r"\bcommoditie\b", "commodity"),
    (r"\bimploy\b", "employ"),
    (r"\bimployed\b", "employed"),
    (r"\bimployment\b", "employment"),
    (r"\btravell\b", "travel"),
    (r"\btraveller\b", "traveler"),
    (r"\btravellers\b", "travelers"),
    (r"\bphilosophick\b", "philosophic"),
    (r"\bpolitically\b", "politically"),
    (r"\bmony\b", "money"),
    (r"\btyme\b", "time"),
    (r"\bcryme\b", "crime"),
]


def is_page_marker(line: str) -> bool:
    """Return True if the line is a PDF page marker that must be preserved."""
    return bool(PAGE_MARKER_PATTERN.match(line.strip()))


def is_ocr_status(line: str) -> bool:
    """Return True if the line is an OCR failure/missing-text marker."""
    stripped = line.strip()
    return (
        stripped == "There is no visible text on this page."
        or stripped == "(No text visible)"
        or bool(OCR_FAILED_PATTERN.match(stripped))
    )


def load_lines(path: Path) -> List[str]:
    """Load a text file into a list of lines without trailing newlines."""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return handle.read().splitlines()


def collect_running_headers(lines: Sequence[str]) -> set[str]:
    """Return lines considered running headers/footers based on frequency."""
    counts: dict[str, int] = {}

    for line in lines:
        stripped = line.strip()
        if not stripped or is_page_marker(stripped) or is_ocr_status(stripped):
            continue
        if RUNNING_HEADER_CANDIDATE.match(stripped):
            counts[stripped] = counts.get(stripped, 0) + 1

    return {text for text, count in counts.items() if count >= 3}


def remove_headers_and_page_numbers(
    lines: Sequence[str], running_headers: set[str]
) -> List[str]:
    """Remove detected running headers and bare page numbers/roman numerals."""
    cleaned: List[str] = []

    for line in lines:
        stripped = line.strip()

        if is_page_marker(line) or is_ocr_status(line):
            cleaned.append(line.rstrip("\n"))
            continue

        if stripped in running_headers:
            continue

        if BARE_PAGE_NUMBER.match(stripped) or BARE_ROMAN_NUMERAL.match(stripped):
            continue

        cleaned.append(line.rstrip("\n"))

    return cleaned


def is_heading_candidate(
    line: str, prev_line: str | None, next_line: str | None, running_headers: set[str]
) -> bool:
    """Determine if a line looks like a heading that should be marked."""
    stripped = line.strip()
    if (
        not stripped
        or is_page_marker(stripped)
        or is_ocr_status(stripped)
        or stripped in running_headers
    ):
        return False

    if len(stripped.split()) > 10:
        return False

    if not (HEADING_ALL_CAPS.match(stripped) or HEADING_NUMBERED.match(stripped)):
        return False

    # Prefer lines that are visually separated by whitespace.
    prev_blank = prev_line is None or not prev_line.strip()
    next_blank = next_line is None or not next_line.strip()
    return prev_blank or next_blank


def mark_headings(lines: Sequence[str], running_headers: set[str]) -> List[str]:
    """Convert heading-like lines to Markdown-style (# / ##) headings."""
    marked: List[str] = []
    total = len(lines)

    for idx, line in enumerate(lines):
        prev_line = lines[idx - 1] if idx > 0 else None
        next_line = lines[idx + 1] if idx + 1 < total else None

        if is_heading_candidate(line, prev_line, next_line, running_headers):
            stripped = line.strip()
            level = "# " if len(stripped) < 25 else "## "
            marked.append(f"{level}{stripped}")
        else:
            marked.append(line)

    return marked


def apply_typo_replacements(text: str) -> str:
    """Apply deterministic typographic and Unicode replacements."""
    for pattern, replacement in TYPO_REPLACEMENTS:
        text = re.sub(pattern, replacement, text)
    return text


def apply_ocr_replacements(text: str) -> str:
    """Apply deterministic OCR error corrections."""
    for pattern, replacement in OCR_REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def apply_modern_spellings(text: str) -> str:
    """Modernize specific archaic spellings to standard forms."""
    for pattern, replacement in MODERN_SPELLINGS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def normalize_paragraph(text: str) -> str:
    """Collapse whitespace and apply minimal punctuation spacing fixes."""
    text = apply_typo_replacements(text)
    text = apply_ocr_replacements(text)
    text = apply_modern_spellings(text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\.(\S)", r". \1", text)
    return text


def flush_paragraph(buffer: List[str], output: List[str]) -> None:
    """Flush the current paragraph buffer into the output list."""
    if not buffer:
        return
    paragraph = " ".join(buffer)
    normalized = normalize_paragraph(paragraph)
    if normalized:
        output.append(normalized)
    buffer.clear()


def build_paragraphs(lines: Sequence[str]) -> List[str]:
    """Merge lines into paragraphs, handling hyphenation and structure."""
    output: List[str] = []
    paragraph: List[str] = []
    idx = 0

    while idx < len(lines):
        line = lines[idx]

        if is_page_marker(line) or is_ocr_status(line):
            flush_paragraph(paragraph, output)
            output.append(line.strip())
            idx += 1
            continue

        if line.startswith("# "):
            flush_paragraph(paragraph, output)
            output.append(line.strip())
            output.append("")
            idx += 1
            continue

        stripped = line.strip()
        if not stripped:
            flush_paragraph(paragraph, output)
            if output and output[-1] != "":
                output.append("")
            idx += 1
            continue

        next_line = lines[idx + 1] if idx + 1 < len(lines) else None
        ends_with_hyphen = bool(re.search(r"-\s*$", stripped))
        can_join_next = (
            next_line is not None
            and not is_page_marker(next_line)
            and not is_ocr_status(next_line)
            and not next_line.lstrip().startswith("#")
            and bool(next_line.strip())
        )

        if ends_with_hyphen and can_join_next:
            next_stripped = next_line.lstrip()
            if re.match(r"^[a-z]", next_stripped):
                combined = re.sub(r"-\s*$", "", stripped) + next_stripped
                paragraph.append(combined)
                idx += 2
                continue
            if re.match(r"^[A-Z]", next_stripped):
                combined = stripped.rstrip() + next_stripped
                paragraph.append(combined)
                idx += 2
                continue

        paragraph.append(stripped)
        idx += 1

    flush_paragraph(paragraph, output)
    return output


def build_metadata_header(source: Path) -> str:
    """Create the YAML-like metadata header for the cleaned file."""
    source_file = source.name
    source_id = source.stem
    header_lines = [
        "---",
        f"source_file: {source_file}",
        f"source_id: {source_id}",
        'notes: "Cleaned using regex-only pipeline; preserved page markers and OCR-status lines."',
        "---",
        "",
    ]
    return "\n".join(header_lines) + "\n"


def clean_text_content(lines: Sequence[str]) -> List[str]:
    """Run the full cleaning pipeline on raw lines."""
    running_headers = collect_running_headers(lines)
    without_headers = remove_headers_and_page_numbers(lines, running_headers)
    marked_headings = mark_headings(without_headers, running_headers)
    return build_paragraphs(marked_headings)


def process_file(path: Path) -> str:
    """Clean a TXT file and return the full output string with metadata."""
    lines = load_lines(path)
    cleaned_lines = clean_text_content(lines)
    body = "\n".join(cleaned_lines).rstrip()
    meta = build_metadata_header(path)
    return meta + body + "\n"


def derive_output_path(input_path: Path) -> Path:
    """Return the output path with --clean appended before the suffix."""
    return input_path.with_name(f"{input_path.stem}--clean{input_path.suffix}")


def prompt_recursive_if_needed(has_directory: bool, flag_value: bool | None) -> bool:
    """
    Ask the user whether to process directories recursively when needed.

    If flag_value is provided, it is used directly; otherwise prompt once.
    """
    if not has_directory:
        return False
    if flag_value is not None:
        return flag_value

    answer = input("Process directories recursively? [y/N]: ").strip().lower()
    return answer.startswith("y")


def discover_txt_files(paths: Sequence[Path], recursive: bool) -> List[Path]:
    """Find TXT files under given paths, skipping files already marked as --clean."""
    discovered: List[Path] = []

    for path in paths:
        if path.is_file():
            if path.suffix.lower() == ".txt" and "--clean" not in path.stem:
                discovered.append(path)
            else:
                print(f"Skipping {path}: not a TXT file or already cleaned")
            continue

        if path.is_dir():
            iterator = path.rglob("*.txt") if recursive else path.glob("*.txt")
            for candidate in iterator:
                if "--clean" in candidate.stem:
                    continue
                if candidate.is_file():
                    discovered.append(candidate)
            continue

        print(f"Skipping {path}: not a file or directory")

    return discovered


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Clean historical OCR TXT files using regex-only rules."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="TXT file(s) or directory(ies) containing TXT (default: current directory)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Process directories recursively (skips prompt)",
    )
    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Process directories non-recursively (skips prompt)",
    )
    parser.set_defaults(recursive=None)
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.paths:
        args.paths = [Path(".")]

    has_directory = any(path.is_dir() for path in args.paths)
    recursive = prompt_recursive_if_needed(has_directory, args.recursive)

    inputs = discover_txt_files(args.paths, recursive=recursive)
    if not inputs:
        print("No TXT files to process (skipping files that already contain --clean).")
        return

    for input_path in inputs:
        output_path = derive_output_path(input_path)
        cleaned_text = process_file(input_path)
        output_path.write_text(cleaned_text, encoding="utf-8", newline="\n")
        print(f"Cleaned: {input_path} -> {output_path}")


if __name__ == "__main__":
    main()
