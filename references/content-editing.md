# Content Editing Reference

XML patterns for populating template slides with real content.

---

## Core Editing Rules

**Preferred method:** Use `str_replace` to make targeted replacements in slide XML.
Best for single unique text blocks where the old string appears exactly once.

**Acceptable method:** Use Python for batch replacements when many values need
changing in one slide. Always write the file back atomically:

```python
with open('/home/claude/unpacked/ppt/slides/slide2.xml', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('<a:t>OLD TEXT</a:t>', '<a:t>NEW TEXT</a:t>', 1)
with open('/home/claude/unpacked/ppt/slides/slide2.xml', 'w', encoding='utf-8') as f:
    f.write(content)
```

**Never use:** `sed`, `awk`, or regex on slide XML — these corrupt namespace
declarations and run-property attributes unpredictably.

---

## Title Replacement

Locate the title shape:
```bash
grep -n 'type="title"' /home/claude/unpacked/ppt/slides/slide2.xml
```

Replace content and ensure bold:
```xml
<a:r>
  <a:rPr lang="en-US" sz="3600" b="1" dirty="0"/>
  <a:t>Q3 Business Review: Key Findings</a:t>
</a:r>
```

Title length guide: ≤ 40 characters. Titles over 50 chars almost always overflow.
Make them descriptive: "Revenue Grew 40% YoY" beats "Financial Results".

---

## Bullet Content

Always create separate `<a:p>` elements per bullet. Never concatenate.

**Correct:**
```xml
<a:p>
  <a:pPr marL="342900" indent="-342900"><a:buChar char="•"/></a:pPr>
  <a:r><a:rPr lang="en-US" sz="1800" dirty="0"/><a:t>Revenue grew 40% YoY</a:t></a:r>
</a:p>
<a:p>
  <a:pPr marL="342900" indent="-342900"><a:buChar char="•"/></a:pPr>
  <a:r><a:rPr lang="en-US" sz="1800" dirty="0"/><a:t>Customer retention at 94%</a:t></a:r>
</a:p>
```

**Wrong — never do this:**
```xml
<a:p><a:r><a:t>• Revenue grew 40%  • Retention at 94%</a:t></a:r></a:p>
```

Always copy `<a:pPr>` from the original paragraph to preserve line spacing,
indentation, and alignment.

Max 5 bullets per slide. If you have 6+, split across two slides or group
into categories.

---

## Big Stat / Callout

```xml
<!-- Large number — use accent color, bold -->
<a:r>
  <a:rPr lang="en-US" sz="8000" b="1" dirty="0">
    <a:solidFill><a:schemeClr val="accent1"/></a:solidFill>
  </a:rPr>
  <a:t>40%</a:t>
</a:r>

<!-- Supporting label — smaller, inherits theme -->
<a:r>
  <a:rPr lang="en-US" sz="1800" dirty="0"/>
  <a:t>Year-over-year revenue growth</a:t>
</a:r>
```

Rules for stat boxes:
- Always include units: "40%" not "40", "$2Bn" not "2"
- One stat per callout box — never compete two numbers in one box
- Never enable autofit on stat boxes — the large sz is part of the design intent
- If the label overflows, **shorten the label text**, not the stat number

---

## Two-Column Slides

Each column is a separate `<p:sp>` text box. Identify by x-offset:
```bash
grep -n 'off x=' /home/claude/unpacked/ppt/slides/slide4.xml
```

Left column: `x` below ~3,000,000 EMU.
Right column: `x` above ~4,500,000 EMU.

Keep both columns within 1 line of each other in length. Unequal column
lengths create visual imbalance. If content is very unequal, redistribute
or use a different layout.

---

## Quote Slides

```xml
<!-- Quote text — italic -->
<a:r>
  <a:rPr lang="en-US" sz="2400" i="1" dirty="0"/>
  <a:t>&#x201C;This solution cut our deployment time in half.&#x201D;</a:t>
</a:r>

<!-- Attribution — bold -->
<a:r>
  <a:rPr lang="en-US" sz="1600" b="1" dirty="0"/>
  <a:t>&#x2014; Jane Smith, CTO, Acme Corp</a:t>
</a:r>
```

Quote length guide: ≤ 25 words. Quotes over 30 words almost always overflow
their containers. Always attribute with: Name, Title, Organization.

Special character XML entities:
- `&#x201C;` = `"` (left double quote)
- `&#x201D;` = `"` (right double quote)
- `&#x2014;` = `—` (em dash)
- `&#x2019;` = `'` (right single quote / apostrophe)
- `&#x2013;` = `–` (en dash)
- `&#x2026;` = `…` (ellipsis)
- `&amp;` = `&`

---

## Preserving Template Formatting

When replacing text, **only replace the `<a:t>` content**. Always keep the
surrounding `<a:pPr>` block intact:

```xml
<!-- KEEP this block unchanged — it controls line spacing and alignment -->
<a:pPr algn="l">
  <a:lnSpc><a:spcPts val="3919"/></a:lnSpc>
  <a:spcAft><a:spcPts val="200"/></a:spcAft>
</a:pPr>

<!-- Only replace the text node inside a:r -->
<a:r>
  <a:rPr lang="en-US" dirty="0"/>
  <a:t>YOUR NEW CONTENT HERE</a:t>
</a:r>
```

---

## Theme References vs. Hardcoding

```xml
<!-- BAD — hardcodes hex color and font name, breaks theme switching -->
<a:rPr lang="en-US" sz="1800" dirty="0">
  <a:solidFill><a:srgbClr val="1F3864"/></a:solidFill>
  <a:latin typeface="Calibri"/>
</a:rPr>

<!-- GOOD — inherits everything from theme -->
<a:rPr lang="en-US" sz="1800" dirty="0"/>

<!-- ALSO GOOD — references theme color slot by name -->
<a:rPr lang="en-US" sz="1800" dirty="0">
  <a:solidFill><a:schemeClr val="accent1"/></a:solidFill>
</a:rPr>
```

Theme color slot names: `dk1`, `lt1`, `dk2`, `lt2`, `accent1`–`accent6`, `hlink`

---

## Removing Excess Template Elements

If a template has 4 feature blocks but you only have 3 items:
- Find the 4th block's `<p:sp>` by shape name or x/y position
- Remove the **entire** `<p:sp>` element (from opening to closing tag)
- Do not leave it with blank text — empty shapes create visual artifacts
  and confuse QA checks

---

## Font Size Reference

`sz` value ÷ 100 = points. Example: `sz="1800"` = 18pt.

| Element            | Typical sz value | Min acceptable |
|--------------------|-----------------|----------------|
| Slide title        | 3200–4400       | 2800           |
| Section header     | 2400–2800       | 2000           |
| Body text          | 1600–2000       | 1200           |
| Caption / footer   | 1000–1400       | 900            |
| Big stat number    | 6000–9600       | 4800           |
| Stat label         | 1400–2000       | 1200           |

---

## Text Overflow — Full Fix Protocol

Text overflow is the **#1 visual failure** in generated presentations. The fix
has four strategies. Use the decision tree to select the right one.

---

### BEFORE Writing: Measure Placeholder Capacity

For every text box you plan to fill, check its dimensions:

```bash
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
        if cx and cy:
            print(f\"{name.get('name','?'):40s}  {cx/914400:.2f}\" x {cy/914400:.2f}\")
"
```

**Safe budget formula:** 80% × (box_height_in / (font_pt × 1.2 / 72)) × (box_width_in / (font_pt × 0.5 / 72))

Quick reference (80% safe budgets):

| Box height | Box width | 14pt budget | 16pt budget | 18pt budget |
|------------|-----------|-------------|-------------|-------------|
| 0.5"       | 3"        | ~50 chars   | ~40 chars   | ~31 chars   |
| 1"         | 3"        | ~124 chars  | ~99 chars   | ~77 chars   |
| 1"         | 4"        | ~165 chars  | ~131 chars  | ~102 chars  |
| 2"         | 3"        | ~248 chars  | ~198 chars  | ~154 chars  |
| 2"         | 4"        | ~330 chars  | ~264 chars  | ~205 chars  |
| 3"         | 4"        | ~496 chars  | ~396 chars  | ~308 chars  |
| 4"         | 4"        | ~661 chars  | ~528 chars  | ~410 chars  |

**Rule: If planned text exceeds the budget, shorten it BEFORE writing XML.**

Run the automated audit at any time:
```bash
python /mnt/skills/user/generating-pptx-from-template/scripts/audit_overflow.py \
  /home/claude/unpacked/ppt/slides/
```

---

### Fix Strategy A — Enable Autofit (Best for body/description boxes)

The cleanest fix: let PowerPoint shrink text automatically to fit the box.
Locate the `<a:bodyPr>` of the overflowing shape and change its autofit child:

```xml
<!-- BEFORE: no autofit (text gets clipped) -->
<a:bodyPr>
  <a:noAutofit/>
</a:bodyPr>

<!-- AFTER: shrinks font proportionally to fit, box size unchanged -->
<a:bodyPr>
  <a:normAutofit/>
</a:bodyPr>
```

If `<a:bodyPr>` has no child element, or if `<a:noAutofit/>` is missing, add it:
```xml
<!-- Add normAutofit as the first child of bodyPr -->
<a:bodyPr wrap="square" rtlCol="0">
  <a:normAutofit/>
</a:bodyPr>
```

**Use autofit for:** body text, bullets, description boxes, caption boxes,
any box where font can scale down 1–4pt without harming readability.

**Do NOT use autofit for:** title shapes, big stat numbers, brand callouts,
or any box where a specific `sz` value is intentional to the design.

---

### Fix Strategy B — Manually Reduce Font Size

When `sz` is explicitly set and autofit is not appropriate, reduce it directly:

```xml
<!-- Original — overflowing at 20pt -->
<a:rPr lang="en-US" sz="2000" dirty="0"/>

<!-- Fixed — reduced to 16pt -->
<a:rPr lang="en-US" sz="1600" dirty="0"/>
```

**How much to reduce:**

| Content vs. capacity ratio | Reduction                          |
|----------------------------|------------------------------------|
| 101–110% (barely over)     | Drop sz by 100 (1pt)               |
| 111–125% (moderately over) | Drop sz by 200–300 (2–3pt)         |
| 126–150% (significantly)   | Drop sz by 400–500 + shorten text  |
| > 150% (major overflow)    | Shorten content AND reduce sz      |

**Minimum readable sizes:** body 1200 (12pt), captions 1000 (10pt).
If reducing below these limits, use Strategy D (shorten content) instead.

After reducing, re-run the audit and re-render to confirm the fix.

---

### Fix Strategy C — Expand the Text Box Height

When content cannot be shortened and the template has physical space below
the text box, increase the box's `cy` (height) value:

```xml
<!-- Original — 914,400 EMU = 1 inch -->
<a:ext cx="2743200" cy="914400"/>

<!-- Expanded — 1,828,800 EMU = 2 inches -->
<a:ext cx="2743200" cy="1828800"/>
```

**EMU conversion:** 1 inch = 914,400 EMU. So 1.5" = 1,371,600 EMU.

**Before expanding, verify:**
1. Check the `off y` position of the shape and of the shape directly below it
2. Confirm `(off_y + new_cy)` does not exceed `off_y` of the shape below
3. If it would overlap, either reduce the expansion or use Strategy D instead

Always re-render after expanding to confirm no new overlaps were created.

---

### Fix Strategy D — Shorten the Content

When all other strategies are constrained (stat box, tight design, no space),
rewrite the text to fit the available space.

**Shortening techniques:**

| Verbose form | Shortened form |
|---|---|
| "is projected to reach ... by 2030" | "→ $X by 2030" |
| "grew from $X to $Y" | "$X → $Y" |
| "USD 50 billion" | "$50Bn" |
| "compound annual growth rate of 12%" | "12% CAGR" |
| "is expected to increase significantly" | "↑ significantly" |
| "year-over-year" | "YoY" |
| "quarter-over-quarter" | "QoQ" |

**Rules:**
- Remove filler phrases: "it is worth noting that", "as we can see", "in terms of"
- Use symbols: `→` `↑` `↓` `%` `$` `×` `+` `–`
- Drop units when context makes them obvious ("Revenue: $2Bn, $3Bn, $4Bn")
- Max 1 idea per sentence in a body box
- Stat labels: max 4 words. "Online Fashion CAGR 2024–29" not the full sentence

---

### Decision Tree: Which Strategy to Apply

```
Is the overflowing box a body / description / bullet box?
  YES → Apply Strategy A (normAutofit). Re-render. Done.
  NO  ↓

Is it a stat number, title, or design-critical callout?
  YES → Apply Strategy D (shorten text). Re-render. Done.
  NO  ↓

Is there empty vertical space below the box (no shape within 0.25")?
  YES → Apply Strategy C (expand cy) + Strategy A (normAutofit). Done.
  NO  ↓

Apply Strategy B (reduce sz) + Strategy D (shorten text) together.
Re-render. If still overflowing, reduce sz one more step.
```

---

### Overflow QA Checklist

Run after every visual render. Check each slide image:

- [ ] No text cut off at the bottom of any box
- [ ] No text overlapping an adjacent shape or image
- [ ] No stat numbers clipped mid-digit
- [ ] Title text fully visible and not truncated mid-word
- [ ] All bullet points visible including the last one
- [ ] Small caption and footer boxes not bleeding into other zones
- [ ] Two-column slides have roughly equal column heights

If any item fails: apply the decision tree, re-pack, re-render, re-check.

---

## Whitespace Preservation

For text with intentional leading or trailing spaces:
```xml
<a:t xml:space="preserve"> text with leading space</a:t>
```
