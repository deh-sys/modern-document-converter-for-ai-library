#!/usr/bin/env python3
"""
Analyze sample caselaw files to identify patterns for filename extraction.
"""

import os
import subprocess
import json
import re
from pathlib import Path

SAMPLE_DIR = "/Users/dan/Projects/file-renamer-caselaw/sample_files"

def extract_pdf_text(pdf_path, max_pages=2):
    """Extract text from first N pages of a PDF, excluding headers/footers."""
    try:
        # Extract first 2 pages
        result = subprocess.run(
            ['pdftotext', '-f', '1', '-l', str(max_pages), '-layout', pdf_path, '-'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout
    except Exception as e:
        return f"Error extracting text: {e}"

def analyze_filename_pattern(filename):
    """Identify pattern elements in the filename."""
    patterns = {
        'has_prefix': bool(re.match(r'^law\s*-\s*', filename)),
        'has_parenthetical': bool(re.search(r'\([^)]+\d{4}\)', filename)),
        'has_reporter_citation': bool(re.search(r'LEXIS|WL|F\.\d+d|S\.Ct\.|U\.S\.', filename)),
        'has_artifact': bool(re.search(r'_Attachment|_Draft', filename)),
    }

    # Try to extract components
    components = {
        'prefix': None,
        'case_name': None,
        'court_from_filename': None,
        'year_from_filename': None,
        'reporter_from_filename': None,
    }

    # Strip prefix if present
    clean_name = filename
    if patterns['has_prefix']:
        match = re.match(r'^law\s*-\s*([A-Z\s]+)\s*-\s*(.+)$', filename)
        if match:
            components['prefix'] = 'law'
            jurisdiction_hint = match.group(1).strip()
            clean_name = match.group(2)
            components['jurisdiction_hint'] = jurisdiction_hint

    # Extract parenthetical (court + year)
    paren_match = re.search(r'\(([^)]+)\s+(\d{4})\)', clean_name)
    if paren_match:
        components['court_from_filename'] = paren_match.group(1).strip()
        components['year_from_filename'] = paren_match.group(2)
        # Extract case name (everything before the parenthetical)
        components['case_name'] = clean_name[:paren_match.start()].strip()

    # Look for LEXIS citation pattern
    lexis_match = re.search(r'(\d{4})\s+U\.S\.\s+Dist\.\s+LEXIS\s+(\d+)', clean_name)
    if lexis_match:
        components['year_from_filename'] = lexis_match.group(1)
        components['reporter_from_filename'] = 'U.S. Dist. LEXIS'
        # Extract case name (everything before year)
        components['case_name'] = clean_name[:lexis_match.start()].strip().rstrip('_')

    # Remove artifacts
    if components['case_name']:
        components['case_name'] = re.sub(r'_Attachment\d*', '', components['case_name'])

    return patterns, components

def find_case_caption(text):
    """Find the official case caption in the PDF text."""
    lines = text.split('\n')

    # Look for "v." or "vs." pattern which typically indicates case name
    for i, line in enumerate(lines[:30]):  # Check first 30 lines
        if re.search(r'\s+v\.?\s+', line, re.IGNORECASE):
            # Get context around it
            context = '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
            return context
    return None

def find_court_and_date(text):
    """Extract court name and decision date from PDF text, avoiding download dates in margins."""
    # Strategy: Look in the main body, avoid single lines at top/bottom that look like headers
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    results = {
        'court': None,
        'date': None,
        'reporter_citation': None
    }

    # Look for court indicators (typically in first 20 lines of main content)
    court_patterns = [
        r'UNITED STATES DISTRICT COURT',
        r'COURT OF APPEALS',
        r'SUPREME COURT',
        r'DISTRICT COURT',
        r'SUPERIOR COURT',
        r'STATE COURT',
    ]

    for i, line in enumerate(lines[:40]):
        for pattern in court_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Grab surrounding context
                results['court'] = '\n'.join(lines[i:min(i+3, len(lines))])
                break
        if results['court']:
            break

    # Look for "Decided: Month Day, Year" or "Filed: Month Day, Year" patterns
    # Avoid single-line dates that look like they're in margins
    date_patterns = [
        r'(?:Decided|Filed|Dated):\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',
        r'(?:Decided|Filed|Dated)\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',
        # Also look for standalone date in case caption area
        r'\b([A-Z][a-z]+\s+\d{1,2},\s+\d{4})\b',
    ]

    for i, line in enumerate(lines[:50]):
        # Skip lines that are very short (likely margins) unless they have context words
        if len(line) < 20 and not re.search(r'(?:Decided|Filed|Dated)', line, re.IGNORECASE):
            continue

        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                results['date'] = match.group(1)
                # If we found a labeled date (Decided/Filed), prefer it and stop
                if 'Decided' in line or 'Filed' in line:
                    break
        if results['date'] and ('Decided' in line or 'Filed' in line):
            break

    # Look for reporter citation
    reporter_patterns = [
        r'\d+\s+F\.\s*Supp\.\s*\d*d?\s+\d+',
        r'\d+\s+F\.\s*\d*d\s+\d+',
        r'\d+\s+S\.\s*Ct\.\s+\d+',
        r'\d+\s+U\.S\.\s+\d+',
        r'\d+\s+S\.E\.\s*\d*d\s+\d+',
        r'\d+\s+Ga\.\s*App\.\s+\d+',
        r'\d+\s+Ga\.\s+\d+',
        r'U\.S\.\s+Dist\.\s+LEXIS\s+\d+',
    ]

    for line in lines[:50]:
        for pattern in reporter_patterns:
            match = re.search(pattern, line)
            if match:
                results['reporter_citation'] = match.group(0)
                break
        if results['reporter_citation']:
            break

    return results

def main():
    print("=" * 80)
    print("CASELAW FILENAME PATTERN ANALYSIS")
    print("=" * 80)
    print()

    sample_files = sorted(Path(SAMPLE_DIR).glob("*.pdf"))

    analysis_results = []

    for pdf_file in sample_files:
        filename = pdf_file.stem  # filename without extension
        print(f"\n{'=' * 80}")
        print(f"FILE: {pdf_file.name}")
        print(f"{'=' * 80}")

        # Analyze filename
        patterns, components = analyze_filename_pattern(filename)

        print(f"\n--- FILENAME ANALYSIS ---")
        print(f"Patterns detected: {json.dumps(patterns, indent=2)}")
        print(f"\nComponents extracted from filename:")
        for key, value in components.items():
            if value:
                print(f"  {key}: {value}")

        # Extract and analyze PDF text
        print(f"\n--- PDF TEXT ANALYSIS ---")
        pdf_text = extract_pdf_text(str(pdf_file), max_pages=2)

        # Find case caption
        caption = find_case_caption(pdf_text)
        if caption:
            print(f"Case caption found:")
            print(f"  {caption[:200]}...")

        # Find court and date
        pdf_info = find_court_and_date(pdf_text)
        print(f"\nExtracted from PDF:")
        for key, value in pdf_info.items():
            if value:
                print(f"  {key}: {value}")

        # Save results
        analysis_results.append({
            'filename': pdf_file.name,
            'filename_components': components,
            'pdf_info': pdf_info,
        })

        print()

    # Save results to JSON
    output_file = "/Users/dan/Projects/file-renamer-caselaw/sample_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2)

    print(f"\n{'=' * 80}")
    print(f"Analysis complete. Results saved to: {output_file}")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    main()
