#!/usr/bin/env python3
"""
audit_overflow.py
Scans unpacked slide XML files and reports text boxes that are likely
to overflow based on placeholder dimensions vs. content length.

For each risky placeholder: slide file, shape name, box dimensions,
character count, current font size, overflow ratio, and recommended
maximum font size.

Usage:
    python audit_overflow.py /home/claude/unpacked/ppt/slides/
    python audit_overflow.py /home/claude/unpacked/ppt/slides/slide2.xml

Exit codes:
    0 — no overflows detected (AT RISK items may still exist)
    1 — one or more OVERFLOW items found (must fix before delivering)
    2 — usage error
"""

import sys
import os
import re
import xml.etree.ElementTree as ET

NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}

EMU_PER_INCH = 914_400
PT_PER_INCH  = 72


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def emu_to_inches(emu: int) -> float:
    return emu / EMU_PER_INCH


def capacity(width_emu: int, height_emu: int, font_pt: float) -> int:
    """
    Estimate max characters that fit in a text box.

    Assumptions:
      - Line height  ≈ font_pt × 1.2  (includes leading)
      - Char width   ≈ font_pt × 0.5  (average proportional font)
    Returns total character capacity (not accounting for word-wrap gaps).
    """
    if font_pt <= 0:
        font_pt = 18.0  # safe fallback
    w_in = emu_to_inches(width_emu)
    h_in = emu_to_inches(height_emu)
    line_h = (font_pt * 1.2) / PT_PER_INCH
    chars_per_line = max(1, int(w_in / ((font_pt * 0.5) / PT_PER_INCH)))
    max_lines = max(1, int(h_in / line_h))
    return max_lines * chars_per_line


def recommend_font_pt(char_count: int, width_emu: int, height_emu: int) -> float:
    """Find the largest font size (pt) at which char_count fits at 80% capacity."""
    for pt in range(36, 8, -1):
        if char_count <= capacity(width_emu, height_emu, pt) * 0.80:
            return float(pt)
    return 8.0  # absolute minimum


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def get_autofit(sp_elem) -> str:
    """Return the autofit mode of a shape: normAutofit | noAutofit | spAutoFit | default"""
    bp = sp_elem.find('.//a:bodyPr', NS)
    if bp is None:
        return 'default'
    if bp.find('a:normAutofit', NS) is not None:
        return 'normAutofit'
    if bp.find('a:noAutofit', NS) is not None:
        return 'noAutofit'
    if bp.find('a:spAutoFit', NS) is not None:
        return 'spAutoFit'
    return 'default'


def get_text_and_fontsize(sp_elem):
    """
    Returns (full_text: str, dominant_font_pt: float).
    dominant_font_pt is 0.0 if inherited (no sz attribute found).
    """
    texts, sizes = [], []
    for t in sp_elem.findall('.//a:t', NS):
        if t.text:
            texts.append(t.text)
    for rpr in sp_elem.findall('.//a:rPr', NS):
        sz = rpr.get('sz')
        if sz:
            try:
                sizes.append(int(sz))
            except ValueError:
                pass
    full_text = ' '.join(texts)
    font_pt = (sizes[0] / 100.0) if sizes else 0.0
    return full_text, font_pt


def is_title_shape(sp_elem) -> bool:
    """Returns True if the shape is a title placeholder."""
    ph = sp_elem.find('.//p:ph', NS)
    return ph is not None and ph.get('type') == 'title'


# ---------------------------------------------------------------------------
# Per-slide audit
# ---------------------------------------------------------------------------

def audit_slide(slide_path: str) -> list:
    issues = []
    try:
        tree = ET.parse(slide_path)
        root = tree.getroot()
    except ET.ParseError as e:
        return [{'file': slide_path, 'error': str(e)}]

    for sp in root.findall('.//p:sp', NS):
        cNvPr = sp.find('.//p:cNvPr', NS)
        shape_name = cNvPr.get('name', 'unknown') if cNvPr is not None else 'unknown'

        xfrm = sp.find('.//a:xfrm', NS)
        if xfrm is None:
            continue
        ext = xfrm.find('a:ext', NS)
        if ext is None:
            continue
        try:
            cx = int(ext.get('cx', 0))
            cy = int(ext.get('cy', 0))
        except (ValueError, TypeError):
            continue
        if cx == 0 or cy == 0:
            continue

        text, font_pt = get_text_and_fontsize(sp)
        if not text.strip():
            continue

        actual_chars = len(text.strip())
        fallback_pt  = font_pt if font_pt > 0 else 18.0
        cap          = capacity(cx, cy, fallback_pt)
        ratio        = actual_chars / cap if cap > 0 else 999.0
        autofit      = get_autofit(sp)
        title_shape  = is_title_shape(sp)

        # Flag at > 85% capacity
        if ratio > 0.85:
            rec_pt = recommend_font_pt(actual_chars, cx, cy)
            status = 'OVERFLOW' if ratio > 1.0 else 'AT RISK'

            # Determine best fix suggestion
            if autofit == 'normAutofit':
                fix_hint = 'Already has normAutofit — content will shrink; verify visually'
            elif title_shape:
                fix_hint = 'Title shape — shorten text content (never autofit titles)'
            elif autofit in ('noAutofit', 'default'):
                fix_hint = 'Add <a:normAutofit/> to <a:bodyPr>, OR reduce sz, OR shorten text'
            else:
                fix_hint = 'Review — spAutoFit will grow box; may overlap adjacent shapes'

            issues.append({
                'file':          os.path.basename(slide_path),
                'shape':         shape_name,
                'is_title':      title_shape,
                'autofit':       autofit,
                'width_in':      round(emu_to_inches(cx), 2),
                'height_in':     round(emu_to_inches(cy), 2),
                'font_pt':       font_pt if font_pt > 0 else '(inherited)',
                'chars':         actual_chars,
                'capacity':      cap,
                'overflow_ratio': round(ratio, 2),
                'status':        status,
                'rec_font_pt':   rec_pt,
                'fix_hint':      fix_hint,
                'preview':       text.strip()[:70] + ('…' if len(text.strip()) > 70 else ''),
            })

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python audit_overflow.py <slides_dir_or_slide.xml>")
        sys.exit(2)

    target = sys.argv[1]
    slide_files = []

    if os.path.isdir(target):
        for fname in sorted(os.listdir(target)):
            if fname.startswith('slide') and fname.endswith('.xml') and '_rels' not in fname:
                slide_files.append(os.path.join(target, fname))
    elif os.path.isfile(target) and target.endswith('.xml'):
        slide_files = [target]
    else:
        print(f"ERROR: {target!r} is not a directory or .xml file")
        sys.exit(2)

    if not slide_files:
        print("No slide XML files found.")
        sys.exit(0)

    all_issues = []
    for path in slide_files:
        all_issues.extend(audit_slide(path))

    if not all_issues:
        print("✓  No overflow risks detected across all slides.")
        sys.exit(0)

    overflows = [i for i in all_issues if i.get('status') == 'OVERFLOW']
    at_risk   = [i for i in all_issues if i.get('status') == 'AT RISK']

    print(f"\n{'='*72}")
    print(f"  OVERFLOW AUDIT  —  {len(overflows)} overflow(s), {len(at_risk)} at-risk box(es)")
    print(f"{'='*72}\n")

    for issue in sorted(all_issues, key=lambda x: x.get('overflow_ratio', 0), reverse=True):
        status  = issue.get('status', '?')
        marker  = '🔴 OVERFLOW' if status == 'OVERFLOW' else '🟡 AT RISK '
        title_m = '  [TITLE]' if issue.get('is_title') else ''
        fit_m   = f"  autofit={issue['autofit']}"

        print(f"{marker}  {issue['file']}  ›  {issue['shape']}{title_m}")
        print(f"         Box: {issue['width_in']}\" × {issue['height_in']}\"  |  "
              f"Font: {issue['font_pt']}pt{fit_m}")
        print(f"         Chars: {issue['chars']} used / {issue['capacity']} capacity  |  "
              f"Ratio: {issue['overflow_ratio']:.0%}")
        print(f"         Recommended max font: {issue['rec_font_pt']}pt")
        print(f"         Fix: {issue['fix_hint']}")
        print(f"         Preview: \"{issue['preview']}\"")
        print()

    # Summary
    print(f"{'─'*72}")
    if overflows:
        print(f"❌  {len(overflows)} OVERFLOW(S) must be fixed before delivering.")
        print(f"    Fixes: normAutofit | reduce sz | expand cy | shorten text")
    else:
        print(f"✓  No overflows. Review {len(at_risk)} AT RISK item(s) in the visual render.")
    print()

    sys.exit(1 if overflows else 0)


if __name__ == '__main__':
    main()
