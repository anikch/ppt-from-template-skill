#!/usr/bin/env python3
"""
check_placeholders.py
Scans a packed .pptx file for leftover template placeholder text.
Exits with code 1 if any patterns are found (use as a QA gate).

Usage:
    python check_placeholders.py output.pptx
    python check_placeholders.py output.pptx --strict   # also checks for generic titles

Exit codes:
    0 — clean (no placeholder text found)
    1 — placeholder text found (must fix before delivering)
    2 — usage error
"""

import sys
import subprocess
import re

# Core placeholder patterns — always checked
PLACEHOLDER_PATTERNS = [
    (r"lorem",                         "Lorem ipsum filler text"),
    (r"ipsum",                         "Lorem ipsum filler text"),
    (r"click to (add|edit|enter)",     "Unedited PowerPoint prompt"),
    (r"add (title|subtitle|text)",     "Unedited PowerPoint prompt"),
    (r"(your|the) title (here|goes)",  "Generic title placeholder"),
    (r"title here",                    "Generic title placeholder"),
    (r"heading here",                  "Generic heading placeholder"),
    (r"sample text",                   "Generic sample text"),
    (r"placeholder text",              "Explicit placeholder label"),
    (r"\bxxxx\b",                      "Generic xxxx filler"),
    (r"\b20xx\b",                      "Unreplaced year token"),
    (r"\b20yy\b",                      "Unreplaced year token"),
    (r"\bq[1-4] 20xx\b",              "Unreplaced quarter token"),
    (r"(?<!!)\[(?!image |a |an )[^\]]{3,40}\]", "Square bracket placeholder (e.g., [Company Name])"),
    (r"this (page|slide) (layout|shows)", "Template description text"),
    (r"insert (image|photo|chart|graph) here", "Unreplaced media placeholder"),
    (r"enter (your|the) (name|title|date|company)", "Unreplaced field prompt"),
]

# Strict mode: also catch patterns that may be intentional but are suspicious
STRICT_PATTERNS = [
    (r"\bfabrikam\b",        "Template company name (Fabrikam)"),
    (r"\bcontoso\b",         "Template company name (Contoso)"),
    (r"\badventurer works\b","Template company name (Adventure Works)"),
    (r"\bnorthwind\b",       "Template company name (Northwind)"),
    (r"\bacme corp\b",       "Template company name (Acme)"),
    (r"\bjane (doe|smith)\b","Generic demo name"),
    (r"\bjohn doe\b",        "Generic demo name"),
    (r"www\.example\.com",   "Example URL"),
    (r"info@example\.com",   "Example email"),
    (r"123-456-7890",        "Example phone number"),
    (r"555-0[0-9]{3}",       "Fictional 555 phone number"),
    (r"208 555",             "Template phone number pattern"),
]


def extract_text(pptx_path: str) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "markitdown", pptx_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"WARNING: markitdown exited with code {result.returncode}")
        print(result.stderr[:500])
    return result.stdout.lower()


def scan(text: str, patterns: list) -> list:
    """Returns list of (description, matched_examples) for each pattern that matches."""
    found = []
    for pattern, description in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            examples = list(dict.fromkeys(matches))[:3]  # deduplicated, max 3
            found.append((description, pattern, examples))
    return found


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_placeholders.py <output.pptx> [--strict]")
        sys.exit(2)

    pptx_path = sys.argv[1]
    strict    = '--strict' in sys.argv

    text = extract_text(pptx_path)
    if not text.strip():
        print(f"ERROR: Could not extract text from {pptx_path}")
        sys.exit(2)

    core_issues   = scan(text, PLACEHOLDER_PATTERNS)
    strict_issues = scan(text, STRICT_PATTERNS) if strict else []
    all_issues    = core_issues + strict_issues

    if not all_issues:
        mode = " (strict mode)" if strict else ""
        print(f"✓  PASS: No placeholder text found in {pptx_path}{mode}")
        sys.exit(0)

    print(f"\n{'='*66}")
    print(f"  PLACEHOLDER CHECK  —  {len(all_issues)} issue(s) found in {pptx_path}")
    print(f"{'='*66}\n")

    for description, pattern, examples in core_issues:
        print(f"  🔴 CORE  |  {description}")
        print(f"           Pattern: '{pattern}'")
        print(f"           Found:   {examples}")
        print()

    for description, pattern, examples in strict_issues:
        print(f"  🟡 STRICT|  {description}")
        print(f"           Pattern: '{pattern}'")
        print(f"           Found:   {examples}")
        print()

    print(f"{'─'*66}")
    if core_issues:
        print(f"❌  {len(core_issues)} core issue(s) must be fixed before delivering.")
    if strict_issues:
        print(f"⚠   {len(strict_issues)} strict issue(s): review and replace if unintentional.")
    print()

    sys.exit(1 if core_issues else 0)


if __name__ == "__main__":
    main()
