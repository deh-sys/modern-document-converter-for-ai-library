#!/usr/bin/env python3
"""
Utility that appends a five-letter registry code to selected files or folders.

Features:
- Uses a single fixed registry file to prevent duplicate codes across all uses
- Verifies registry path on startup and creates it if needed
- Prompts for recursion depth (0, integer levels, or all)
- Processes PDFs, Word docs, Markdown (excluding documentation files) plus folders
- Skips files that already contain a registry suffix or match exclusion rules
- Keeps a registry of assigned codes so no suffix is reused
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

# Fixed registry path - this ensures all users reference the same registry
# to prevent duplicate filename codes
REGISTRY_PATH = Path("/Users/dan/LIBRARY_SYSTEM_REGISTRIES/filename-indexing-registry.json")

ALPHABET = [ch for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if ch != "W"]
LETTER_CLASS = "".join(ALPHABET)
SUFFIX_RE = re.compile(rf"----[{LETTER_CLASS}]{{4,5}}$")

ALLOWED_FILE_EXTS = {".pdf", ".doc", ".docx", ".md", ".txt"}
IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".svg",
    ".tif",
    ".tiff",
    ".webp",
    ".heic",
    ".heif",
}
DOC_SKIP_NAMES = {"README", "LICENSE", "CHANGELOG", "CONTRIBUTING"}


def prompt_yes_no(question: str, default: bool = True) -> bool:
    prompt = "[Y/n]" if default else "[y/N]"
    while True:
        answer = input(f"{question} {prompt} ").strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer with 'y' or 'n'.")


def verify_registry_setup() -> None:
    """
    Verify the registry file path on startup.
    Creates directory and file if they don't exist.
    Prompts user to confirm the registry location.
    """
    print("\n" + "=" * 70)
    print("REGISTRY VERIFICATION")
    print("=" * 70)
    print(f"Registry file path: {REGISTRY_PATH}")
    print(f"Registry directory: {REGISTRY_PATH.parent}")

    # Check and create directory if needed
    if not REGISTRY_PATH.parent.exists():
        print(f"\nDirectory does not exist. Creating: {REGISTRY_PATH.parent}")
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        print("Directory created successfully.")
    else:
        print("Registry directory exists.")

    # Check and create file if needed
    if not REGISTRY_PATH.exists():
        print(f"\nRegistry file does not exist. Creating: {REGISTRY_PATH}")
        initial_data = {"next_index": 0, "used_codes": []}
        with REGISTRY_PATH.open("w", encoding="utf-8") as fh:
            json.dump(initial_data, fh, indent=2)
        print("Registry file created successfully.")
    else:
        print("Registry file exists.")

    print("\n" + "-" * 70)
    input("Press Enter to continue or Ctrl+C to cancel...")
    print("=" * 70 + "\n")


def unescape_shell_path(path_str: str) -> str:
    """
    Remove shell escape sequences from a path string.
    When dragging files into terminal, macOS adds backslashes before spaces and special chars.
    This function converts them back to normal characters.

    Examples:
        'My\\ Drive' -> 'My Drive'
        '\\(deh@example.com\\)' -> '(deh@example.com)'
    """
    result = []
    i = 0
    while i < len(path_str):
        if path_str[i] == '\\' and i + 1 < len(path_str):
            # Skip the backslash and take the next character
            result.append(path_str[i + 1])
            i += 2
        else:
            result.append(path_str[i])
            i += 1
    return ''.join(result)


def prompt_paths(arg_paths: Sequence[str] | None) -> List[Path]:
    if arg_paths:
        parsed = [Path(p).expanduser() for p in arg_paths if p.strip()]
    else:
        while True:
            raw = input("Enter one or more file/folder paths separated by commas (press Enter for current directory): ").strip()
            if not raw:
                # Default to current working directory
                parsed = [Path.cwd()]
                break
            # Unescape shell-escaped paths (from drag-and-drop in terminal)
            parsed = [
                Path(unescape_shell_path(piece.strip())).expanduser()
                for piece in raw.split(",")
                if piece.strip()
            ]
            break
    resolved = []
    for path in parsed:
        if not path.exists():
            print(f"Path does not exist and will be ignored: {path}")
            continue
        resolved.append(path.resolve())
    if not resolved:
        raise SystemExit("No valid paths were provided.")
    return resolved


def prompt_recursion_depth(arg_non_recursive: bool | None) -> int | None:
    """
    Return max traversal depth for directories.

    Depth meaning:
    - 0: process only items directly inside provided paths (no deeper subfolders)
    - N: include items up to N levels down
    - None: unlimited ("all")
    """
    if arg_non_recursive:
        return 0

    default_label = "all"
    prompt = (
        "How deep should folders be processed? "
        "Enter 0 for only items in the provided paths, a positive integer for levels down, or 'all'."
    )

    while True:
        raw = input(f"{prompt} [default: {default_label}] ").strip().lower()
        if not raw:
            return None  # default to unlimited
        if raw == "all":
            return None
        if raw.isdigit():
            return int(raw)
        print("Please enter 0, a positive integer, or 'all'.")


def split_name_and_suffix(path: Path) -> tuple[str, str]:
    suffix = "".join(path.suffixes)
    if suffix:
        base = path.name[: -len(suffix)]
    else:
        base = path.name
    return base, suffix


def has_registry_suffix(path: Path) -> bool:
    target = path.name if path.is_dir() else split_name_and_suffix(path)[0]
    return bool(SUFFIX_RE.search(target))


def should_skip_file(path: Path) -> bool:
    if not path.is_file():
        return True
    if path.name.startswith("."):
        return True
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return True
    if suffix not in ALLOWED_FILE_EXTS:
        return True
    stem = path.stem.upper()
    name_upper = path.name.upper()
    if stem in DOC_SKIP_NAMES or name_upper in DOC_SKIP_NAMES:
        return True
    if path.name.startswith("~$"):
        return True
    return False


def should_skip_directory(path: Path) -> bool:
    if not path.is_dir():
        return True
    name = path.name
    if name.startswith("."):
        return True
    return name.upper() in DOC_SKIP_NAMES


def gather_candidates(inputs: Sequence[Path], max_depth: int | None) -> tuple[List[Path], List[Path]]:
    collected: list[Path] = []
    already_tagged: list[Path] = []
    seen: set[Path] = set()

    def consider(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        if has_registry_suffix(path):
            already_tagged.append(path)
            return
        collected.append(path)

    for base in inputs:
        if base.is_file():
            if not should_skip_file(base):
                consider(base)
            continue

        if base.is_dir():
            if not should_skip_directory(base):
                consider(base)

            stack: list[tuple[Path, int]] = []
            try:
                stack.extend((child, 1) for child in base.iterdir())
            except Exception as exc:
                print(f"Skipping traversal of {base}: {exc}")
                continue

            while stack:
                current, depth = stack.pop()
                if max_depth is not None and depth > max_depth:
                    continue
                if current.is_file():
                    if not should_skip_file(current):
                        consider(current)
                    continue

                if current.is_dir():
                    if should_skip_directory(current):
                        continue
                    consider(current)
                    if max_depth is not None and depth >= max_depth:
                        continue
                    try:
                        stack.extend((child, depth + 1) for child in current.iterdir())
                    except Exception as exc:
                        print(f"Skipping traversal of {current}: {exc}")
                        continue
            continue
    collected.sort(key=lambda p: (-len(p.resolve().parts), str(p).lower()))
    return collected, already_tagged


def index_to_code(idx: int) -> str:
    base = len(ALPHABET)
    limit = base**5
    if idx >= limit:
        raise RuntimeError("Registry exhausted: no codes left.")
    digits: list[str] = []
    for _ in range(5):
        digits.append(ALPHABET[idx % base])
        idx //= base
    return "".join(reversed(digits))


@dataclass
class Registry:
    path: Path
    next_index: int
    used_codes: list[str]

    @classmethod
    def load(cls, path: Path) -> "Registry":
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            next_index = int(data.get("next_index", 0))
            used_codes = list(data.get("used_codes", []))
        else:
            next_index = 0
            used_codes = []
            cls(path, next_index, used_codes).save()
        return cls(path, next_index, used_codes)

    def save(self) -> None:
        payload = {"next_index": self.next_index, "used_codes": self.used_codes}
        # Use atomic write: write to temp file, then rename
        # This prevents corruption if the process is interrupted during write
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            with temp_path.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
            # Atomic rename - if this succeeds, the file is guaranteed to be complete
            temp_path.replace(self.path)
        except Exception:
            # Clean up temp file if something went wrong
            if temp_path.exists():
                temp_path.unlink()
            raise

    def request_code(self) -> str:
        code = index_to_code(self.next_index)
        self.next_index += 1
        return code

    def rollback_code(self, code: str) -> None:
        if self.next_index <= 0:
            return
        expected = index_to_code(self.next_index - 1)
        if expected == code:
            self.next_index -= 1

    def commit_code(self, code: str) -> None:
        self.used_codes.append(code)
        self.save()


def rename_target(path: Path, code: str) -> Path:
    if path.is_dir():
        new_name = f"{path.name}----{code}"
        return path.with_name(new_name)
    base, suffix = split_name_and_suffix(path)
    new_name = f"{base}----{code}{suffix}"
    return path.with_name(new_name)


def process_targets(candidates: Sequence[Path], registry: Registry, pre_skipped: Sequence[Path] | None = None) -> None:
    renamed = []
    skipped_existing = list(pre_skipped or [])
    skipped_conflict = []

    for item in candidates:
        if has_registry_suffix(item):
            skipped_existing.append(item)
            continue
        code = registry.request_code()
        try:
            destination = rename_target(item, code)
        except Exception as exc:  # pragma: no cover - safety net
            print(f"Skipping {item} due to error computing name: {exc}")
            registry.rollback_code(code)
            continue
        if destination.exists():
            print(f"Destination already exists, skipping: {destination}")
            skipped_conflict.append(item)
            registry.rollback_code(code)
            continue
        try:
            item.rename(destination)
        except Exception as exc:
            print(f"Failed to rename {item}: {exc}")
            skipped_conflict.append(item)
            registry.rollback_code(code)
            continue
        registry.commit_code(code)
        renamed.append((item, destination, code))
        print(f"{item} -> {destination} [{code}]")

    print("\nSummary")
    print("-------")
    print(f"Renamed: {len(renamed)}")
    print(f"Skipped (already tagged): {len(skipped_existing)}")
    print(f"Skipped (conflicts/errors): {len(skipped_conflict)}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append unique registry codes to filenames or folders."
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        default=None,
        help="Optional list of paths to process. When omitted, the app prompts interactively.",
    )
    parser.add_argument(
        "--non-recursive",
        action="store_true",
        help="Process only top-level items; skips nested subfolders.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    verify_registry_setup()
    registry = Registry.load(REGISTRY_PATH)
    max_depth = prompt_recursion_depth(args.non_recursive)
    depth_label = "all levels (recursive)" if max_depth is None else (
        "top-level only" if max_depth == 0 else f"up to {max_depth} level{'s' if max_depth != 1 else ''} down"
    )
    print(f"Traversal depth: {depth_label}")
    targets = prompt_paths(args.paths)
    candidates, pre_skipped = gather_candidates(targets, max_depth)
    if not candidates:
        print("No matching files or folders found for the given inputs.")
        if pre_skipped:
            process_targets([], registry, pre_skipped)
        return
    print(f"Found {len(candidates)} eligible items.")
    if pre_skipped:
        print(f"Pre-skipped (already tagged): {len(pre_skipped)}")
    process_targets(candidates, registry, pre_skipped)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
