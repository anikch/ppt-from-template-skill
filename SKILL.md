---
name: generating-pptx-from-template
description: "Generates fully populated PowerPoint presentations that inherit the exact colors, fonts, layouts, and branding from a user-supplied .pptx template. Use when the user uploads or references a .pptx template file and asks to create or generate a presentation on a given topic. Triggers on: use my template, create slides from my pptx, generate a deck using my template, fill in my template, make a presentation from the attached file, build slides using my brand template, or when the user shares a .pptx file and wants a polished output matching their brand. Also use when multiple .pptx files are uploaded and the user wants a presentation combining layouts from all of them."
license: MIT
---

# Generating PPTX from Template

Produces polished PowerPoint presentations using an uploaded `.pptx` file as the
design source of truth. The output inherits the template's exact visual identity
— no generic AI aesthetics, no hardcoded colors or fonts.

---

## Setup

Install required tools before any other step:

```bash
pip install "markitdown[pptx]" Pillow defusedxml --break-system-packages -q
which pdftoppm || apt-get install -y poppler-utils -q
```

All helper scripts live in two locations:

```
# Public pptx skill scripts (structural operations)
/mnt/skills/public/pptx/scripts/office/unpack.py
/mnt/skills/public/pptx/scripts/office/pack.py
/mnt/skills/public/pptx/scripts/office/soffice.py
/mnt/skills/public/pptx/scripts/add_slide.py
/mnt/skills/public/pptx/scripts/clean.py
/mnt/skills/public/pptx/scripts/thumbnail.py

# This skill's scripts (QA and analysis)
/mnt/skills/user/generating-pptx-from-template/scripts/audit_overflow.py
/mnt/skills/user/generating-pptx-from-template/scripts/check_placeholders.py
```

---

## Workflow Overview

```
Step 1  →  Ingest template (markitdown + thumbnails + unpack)
Step 2  →  Plan content (layout inventory + slide map)
Step 2.5 → Measure placeholder capacity BEFORE writing any content
Step 3  →  Structural edits (add/remove/reorder slides)
Step 3.5 → Populate content (XML editing with overflow prevention)
Step 4  →  QA (content check + visual render + overflow check)
Step 5  →  Deliver
```

---

## Step 1 — Ingest the Template

Locate and copy the uploaded template:

```bash
ls /mnt/user-data/uploads/*.pptx
cp /mnt/user-data/uploads/YOUR_TEMPLATE.pptx /home/claude/template.pptx
```

Extract all text and structure to understand existing content:

```bash
python -m markitdown /home/claude/template.pptx
```

Generate visual thumbnails — **this is mandatory, not optional**. You must see
the actual layout, colors, design motifs, and photo placement before writing
a single character of content:

```bash
python /mnt/skills/public/pptx/scripts/thumbnail.py \
  /home/claude/template.pptx /home/claude/thumbnails
```

Unpack to XML for editing:

```bash
python /mnt/skills/public/pptx/scripts/office/unpack.py \
  /home/claude/template.pptx /home/claude/unpacked/
```

After unpacking, run a quick structural survey:

```bash
# How many slides?
ls /home/claude/unpacked/ppt/slides/slide*.xml | grep -v _rels

# What layouts does each slide use?
for f in /home/claude/unpacked/ppt/slides/slide*.xml; do
  echo "$f:"; grep -o 'slideLayout[0-9]*' $f/_rels/../_rels/$(basename $f).rels 2>/dev/null || echo "  (no layout ref found)"
done

# What theme colors are defined?
grep -A20 'a:clrScheme' /home/claude/unpacked/ppt/theme/theme1.xml | grep -E 'val=|name='
```

Read `references/template-analysis.md` for full inspection guidance: color
extraction, font detection, placeholder mapping, and capacity estimation.

---

## Step 2 — Plan Content

**Build a written slide plan before touching any XML.** This prevents
structural rework after content has been populated.

For each slide in the plan, record:
- Slide number → source template slide (e.g., "Slide 3 → use slide2.xml layout")
- Topic / section title
- Content type: stat, bullets, quote, two-column, image+text, etc.
- Approximate content length (word/character count estimate)

Rules:
- Use every distinct layout at least once if the content fits
- Never use the same layout for two consecutive content slides
- Match content type to layout (stats → callout, team → multi-column)
- For typical business presentations: 8–12 slides; pitch decks: 10–15

Read `references/content-mapping.md` for layout-to-content matching tables,
standard slide structures (business, pitch, educational, status report), and
content density rules.

---

## Step 2.5 — Measure Placeholder Capacity (Required Before Writing)

**This step must happen before editing any slide XML.**

Text overflow is the most common and most preventable visual failure. Catching
it before writing content avoids multiple fix cycles.

### Measure box dimensions

```bash
# For a specific slide, get all shape names, widths, and heights
python3 -c "
import xml.etree.ElementTree as ET
NS = {'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
tree = ET.parse('/home/claude/unpacked/ppt/slides/slide2.xml')
for sp in tree.findall('.//p:sp', NS):
    name = sp.find('.//p:cNvPr', NS)
    ext  = sp.find('.//a:ext', NS)
    if name is not None and ext is not None:
        cx = int(ext.get('cx',0)); cy = int(ext.get('cy',0))
        print(f\"{name.get('name','?'):40s}  {cx/914400:.2f}\" x {cy/914400:.2f}\")
"
```

### Set a character budget

Use this table to determine how much text fits safely (≤ 80% capacity rule):

| Box height | Box width | Font size | Max lines | Chars/line | Safe budget (80%) |
|------------|-----------|-----------|-----------|------------|-------------------|
| 0.5"       | 3"        | 14pt      | 2         | 31         | ~50               |
| 0.5"       | 4"        | 12pt      | 2         | 48         | ~77               |
| 1"         | 3"        | 14pt      | 5         | 31         | ~124              |
| 1"         | 3"        | 18pt      | 4         | 24         | ~77               |
| 1"         | 4"        | 14pt      | 5         | 41         | ~164              |
| 2"         | 3"        | 14pt      | 10        | 31         | ~248              |
| 2"         | 3"        | 18pt      | 7         | 24         | ~134              |
| 2"         | 4"        | 16pt      | 9         | 34         | ~245              |
| 3"         | 4"        | 16pt      | 13        | 34         | ~354              |
| 4"         | 4"        | 16pt      | 17        | 34         | ~462              |

Formula: `capacity = (height_in / (font_pt * 1.2 / 72)) * (width_in / (font_pt * 0.5 / 72))`

**If your planned text exceeds the 80% budget, shorten it NOW before writing XML.**

### Run the automated audit

After populating slides (before packing), run the overflow audit:

```bash
python /mnt/skills/user/generating-pptx-from-template/scripts/audit_overflow.py \
  /home/claude/unpacked/ppt/slides/
```

This reports every text box as:
- 🔴 **OVERFLOW** — content already exceeds the box (must fix before delivering)
- 🟡 **AT RISK** — content at 85–100% capacity (review visually)
- And provides a recommended maximum font size for each flagged box

Fix all 🔴 items. Visually verify all 🟡 items in the QA render.

See `references/content-editing.md` → **Text Overflow — Full Fix Protocol** for
the complete decision tree covering all four fix strategies:
autofit XML, font size reduction, box expansion, and content shortening.

---

## Step 3 — Structural Edits

**Complete ALL structural operations before editing any content.**
Editing content before structure is done causes XML corruption and lost work.

Structural order:
1. Remove slides not in your plan (edit `<p:sldIdLst>` in `ppt/presentation.xml`)
2. Duplicate slides you need to reuse: `python scripts/add_slide.py unpacked/ slideN.xml`
3. Reorder slides by rearranging `<p:sldId>` entries in `presentation.xml`

After all structural changes, always clean:

```bash
python /mnt/skills/public/pptx/scripts/clean.py /home/claude/unpacked/
```

---

## Step 3.5 — Populate Content

### Editing rules

**Preferred method:** Use `str_replace` to make targeted replacements in slide XML.
This is the safest approach for small, clearly unique text blocks.

**Acceptable method:** Use Python for batch replacements across a slide when
many text values need changing and `str_replace` would require too many
individual calls. Always write the full file back atomically:

```python
with open(slide_path, 'r', encoding='utf-8') as f:
    content = f.read()
# make all replacements
content = content.replace('<a:t>OLD TEXT</a:t>', '<a:t>NEW TEXT</a:t>', 1)
with open(slide_path, 'w', encoding='utf-8') as f:
    f.write(content)
```

**Never use:** `sed`, `awk`, or regex substitutions that modify surrounding XML.
These corrupt namespace declarations and run-property attributes unpredictably.

### Critical XML rules

- Bold all titles and section headers: `b="1"` on `a:rPr`
- Never use unicode bullet characters — use `<a:buChar char="•"/>` or `<a:buAutoNum>`
- Create separate `<a:p>` elements per bullet — never concatenate into one string
- Preserve `a:pPr` blocks (line spacing, indentation, alignment) from originals
- Use theme color references (`<a:schemeClr val="accent1"/>`) not hardcoded hex values
- Remove `<a:latin typeface="..."/>` overrides to inherit theme fonts automatically
- Use XML entities for special characters: `&#x201C;` `&#x201D;` `&#x2014;` `&#x2019;`
- For text with intentional leading/trailing spaces: `<a:t xml:space="preserve"> text</a:t>`

### After populating each slide

Run the overflow audit immediately:
```bash
python /mnt/skills/user/generating-pptx-from-template/scripts/audit_overflow.py \
  /home/claude/unpacked/ppt/slides/
```

Fix all 🔴 OVERFLOW items before moving to the next slide.

### Pack the output

```bash
python /mnt/skills/public/pptx/scripts/office/pack.py \
  /home/claude/unpacked/ \
  /home/claude/output.pptx \
  --original /home/claude/template.pptx
```

---

## Step 4 — QA (Required — Do Not Skip)

### Content check

```bash
# Check for leftover placeholder text
python /mnt/skills/user/generating-pptx-from-template/scripts/check_placeholders.py \
  /home/claude/output.pptx

# Also run a manual scan for common patterns
python -m markitdown /home/claude/output.pptx | \
  grep -iE "lorem|ipsum|click to|placeholder|your title|add text|xxxx|20xx|20yy"
```

Fix any matches before continuing.

### Visual render

```bash
cd /home/claude
python /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
# Inspect: slide-1.jpg, slide-2.jpg, ...
```

### Visual QA checklist — inspect every slide image for:

**Layout & brand:**
- [ ] Template brand elements preserved (colors, fonts, logos, shapes)
- [ ] Background not replaced or overridden
- [ ] Consistent margins (minimum 0.5 inch from edges)
- [ ] Layout variety across slides — not every slide the same structure

**Text overflow — check every text box:**
- [ ] No text cut off at the bottom of any box
- [ ] No stat numbers or titles clipped mid-character or mid-word
- [ ] No text overlapping an adjacent image or shape
- [ ] No small caption/footer boxes overflowing into other zones
- [ ] All bullet points fully visible (last bullet not clipped)

**Content quality:**
- [ ] No leftover placeholder text (lorem, xxxx, "Click to add", etc.)
- [ ] Readable contrast on all text against its background
- [ ] Numbers have units (%, $, Bn) — never bare numbers
- [ ] Titles are descriptive, not generic

### Fixing overflow found in the visual render

1. Match the overflowing shape in the image to its XML using `off x=` / `off y=` coordinates
2. Apply the decision tree from `references/content-editing.md` → Text Overflow section:
   - **Body/description/bullet box** → add `<a:normAutofit/>` to `<a:bodyPr>`
   - **Stat callout or title (design-critical)** → shorten the text content
   - **Spare vertical space available** → increase `cy` in `<a:ext>`
   - **No space to expand** → reduce `sz` by 100–300 per `<a:rPr>` + shorten text
3. Re-pack and re-render the affected slide
4. Confirm fix is resolved before declaring QA passed

**Do not declare success without at least one full fix-and-verify cycle.**

---

## Step 5 — Deliver

```bash
cp /home/claude/output.pptx /mnt/user-data/outputs/presentation.pptx
```

Present `/mnt/user-data/outputs/presentation.pptx` to the user with a brief
summary of what each slide covers.

---

## Multiple Templates

If the user uploads more than one `.pptx` file:

1. Analyze all templates with markitdown and thumbnails
2. Select the richest template (most layout variety, strongest brand) as primary
3. Import unique layouts from secondary templates only when needed

Read `references/multi-template.md` for the full merge procedure including
media file handling, layout reference resolution, and Content_Types.xml registration.

---

## Common Failure Modes

| Problem | Root Cause | Fix |
|---------|-----------|-----|
| Output colors changed | Hardcoded hex in slide XML | Use `<a:schemeClr>` references instead |
| Fonts changed | Hardcoded `<a:latin typeface>` override | Remove the override — let theme inherit |
| Template logos/images missing | Media files moved or deleted | Never delete `ppt/media/`; always use `--original` flag in pack.py |
| Text cut off at box bottom | Content length exceeds box height | Add `<a:normAutofit/>` to `<a:bodyPr>`, or reduce `sz`, or increase `cy` |
| Text overlaps adjacent shape | Box expanded into another shape's lane | Check `off` + `ext` positions; shrink content or reduce `cy` |
| Stat number clipped | Large `sz` + long label doesn't fit box width | Shorten label; reduce stat `sz` by 200–400; never autofit stat boxes |
| Title truncated mid-word | Title text too long for placeholder width | Rewrite title to ≤ 40 chars; reduce sz to minimum 2800 |
| Content unreadably tiny | Over-reduced `sz` to force fit | Expand `cy` if space allows; split content across two slides |
| Wrong slide duplicated | add_slide.py called with wrong source | Confirm source slide filename before duplicating |
| Structural edits lost | Content edited before structure complete | Always complete all add/remove/reorder before any text edits |
| XML corruption | Used sed/awk/regex on XML | Only use str_replace or atomic Python file writes |

---

## Reference Files

| File | Contents |
|------|----------|
| `references/template-analysis.md` | Template inspection: color extraction, font detection, placeholder mapping, capacity estimation |
| `references/content-editing.md` | XML patterns for all content types + full text overflow fix protocol |
| `references/content-mapping.md` | Layout-to-content matching, presentation structures, density rules |
| `references/multi-template.md` | Merging multiple uploaded templates |
| `scripts/audit_overflow.py` | Automated overflow detection: scans slide XML, reports at-risk boxes with recommended font sizes |
| `scripts/check_placeholders.py` | QA gate: scans output for leftover placeholder text patterns |
