# Template Analysis Reference

Deep inspection of an uploaded `.pptx` template before generating content.
Run these checks during Step 1 — before planning any content.

---

## 1. Build a Layout Inventory

After running thumbnails, fill this table for the actual template:

| Slide File | Layout Style | Key Visual Features | Best Used For |
|------------|-------------|---------------------|---------------|
| slide1.xml | Title Slide  | Full-bleed bg, large centered title | Opening |
| slide2.xml | Title + Content | Header + body area | Key points, lists |
| slide3.xml | Section Divider | Label + minimal text | Section breaks |
| slide4.xml | Two-Column | Left / right panels | Comparisons |
| slide5.xml | Big Stat | Oversized number + support text | KPIs, metrics |
| slide6.xml | Image + Text | Photo + content panel | Case studies |
| slide7.xml | Closing | CTA or summary | Final slide |

Fill with actual filenames. Add or remove rows to match the template.

---

## 2. Extract the Color Scheme

Open `ppt/theme/theme1.xml`, locate `<a:clrScheme>`:

```bash
grep -A30 'a:clrScheme' /home/claude/unpacked/ppt/theme/theme1.xml \
  | grep -E 'val=|<a:(dk|lt|accent|hlink)'
```

Example output:
```xml
<a:clrScheme name="Office Theme">
  <a:dk1><a:sysClr lastClr="000000"/></a:dk1>
  <a:lt1><a:sysClr lastClr="FFFFFF"/></a:lt1>
  <a:dk2><a:srgbClr val="1F3864"/></a:dk2>
  <a:lt2><a:srgbClr val="EEECE1"/></a:lt2>
  <a:accent1><a:srgbClr val="4472C4"/></a:accent1>
  <a:accent2><a:srgbClr val="ED7D31"/></a:accent2>
  <a:accent3><a:srgbClr val="A9D18E"/></a:accent3>
</a:clrScheme>
```

Record `dk1`, `lt1`, `dk2`, `lt2`, `accent1`–`accent6`, `hlink`.

**Never hardcode these hex values in slide XML.** Always reference via:
```xml
<a:schemeClr val="accent1"/>
<a:schemeClr val="dk2"/>
```

---

## 3. Extract Fonts

Open `ppt/theme/theme1.xml`, locate `<a:fontScheme>`:

```bash
grep -A10 'a:fontScheme' /home/claude/unpacked/ppt/theme/theme1.xml
```

Example:
```xml
<a:fontScheme>
  <a:majorFont><a:latin typeface="Calibri Light"/></a:majorFont>
  <a:minorFont><a:latin typeface="Calibri"/></a:minorFont>
</a:fontScheme>
```

Record heading font (majorFont) and body font (minorFont).

In slide XML, always inherit fonts via:
```xml
<a:rPr lang="en-US" dirty="0"/>
```

Only hardcode a font (`<a:latin typeface="..."/>`) if the template itself
explicitly sets it on that slide for a specific design reason.

---

## 4. Build a Placeholder Map

For each template slide you plan to use, identify all content areas and their
current autofit settings:

```bash
# Find all placeholders and text boxes
grep -A8 '<p:ph' /home/claude/unpacked/ppt/slides/slide2.xml | \
  grep -E 'type=|idx=|name='

# Find all bodyPr autofit settings (crucial for overflow handling)
grep -n 'bodyPr\|noAutofit\|normAutofit\|spAutoFit' \
  /home/claude/unpacked/ppt/slides/slide2.xml
```

Common placeholder types:
```xml
<p:ph type="title"/>           <!-- slide headline -->
<p:ph type="body" idx="1"/>    <!-- main content area -->
<p:ph type="ftr"/>             <!-- footer — leave inherited -->
<p:ph type="pic"/>             <!-- picture placeholder -->
<p:ph idx="10"/>               <!-- custom — no type attr -->
```

For each placeholder, record:
- `idx` value (used to identify it uniquely)
- Position: `off x=` / `off y=` in EMU
- Size: `cx=` / `cy=` in EMU, then convert to inches (÷ 914400)
- Current autofit: `noAutofit` / `normAutofit` / `spAutoFit` / (missing = default)
- Font sizes in use: scan `sz=` attributes in that shape

This map drives the capacity estimation in Step 2.5.

---

## 5. Measure Text Box Capacity

**Do this for every box you plan to populate.** This is the foundation of
overflow prevention.

### Quick measurement command

```bash
python3 -c "
import xml.etree.ElementTree as ET
NS = {'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
tree = ET.parse('/home/claude/unpacked/ppt/slides/slide2.xml')
for sp in tree.findall('.//p:sp', NS):
    name = sp.find('.//p:cNvPr', NS)
    ext  = sp.find('.//a:ext', NS)
    szs  = [r.get('sz') for r in sp.findall('.//a:rPr', NS) if r.get('sz')]
    bp   = sp.find('.//a:bodyPr', NS)
    fit  = 'normAutofit' if bp is not None and bp.find('{http://schemas.openxmlformats.org/drawingml/2006/main}normAutofit') is not None else \
           'noAutofit' if bp is not None and bp.find('{http://schemas.openxmlformats.org/drawingml/2006/main}noAutofit') is not None else 'default'
    if name is not None and ext is not None:
        cx = int(ext.get('cx',0)); cy = int(ext.get('cy',0))
        if cx and cy:
            sz_str = szs[0] if szs else 'inherited'
            print(f'{name.get(\"name\",\"?\"):42s}  {cx/914400:.2f}\"x{cy/914400:.2f}\"  sz={sz_str}  fit={fit}')
"
```

### Capacity formula

```
line_height_in  = font_pt × 1.2 / 72
chars_per_line  = box_width_in / (font_pt × 0.5 / 72)
max_lines       = box_height_in / line_height_in
total_capacity  = max_lines × chars_per_line
safe_budget     = total_capacity × 0.80
```

### Quick reference table (80% safe budgets)

| Box height | Box width | 12pt | 14pt | 16pt | 18pt | 20pt |
|------------|-----------|------|------|------|------|------|
| 0.5"       | 3"        | ~60  | ~50  | ~40  | ~31  | ~25  |
| 0.5"       | 4"        | ~80  | ~66  | ~53  | ~41  | ~33  |
| 1"         | 3"        | ~150 | ~124 | ~99  | ~77  | ~60  |
| 1"         | 4"        | ~200 | ~165 | ~131 | ~102 | ~80  |
| 1.5"       | 3"        | ~225 | ~186 | ~148 | ~115 | ~90  |
| 2"         | 3"        | ~300 | ~248 | ~198 | ~154 | ~120 |
| 2"         | 4"        | ~400 | ~330 | ~264 | ~205 | ~160 |
| 3"         | 4"        | ~600 | ~496 | ~396 | ~308 | ~240 |
| 4"         | 4"        | ~800 | ~661 | ~528 | ~410 | ~320 |

### Automated capacity audit

Run at any time to get per-shape overflow analysis:
```bash
python /mnt/skills/user/generating-pptx-from-template/scripts/audit_overflow.py \
  /home/claude/unpacked/ppt/slides/
```

Reports: shape name, box dimensions, current font size, content character count,
overflow ratio, and recommended maximum font size.

---

## 6. Check Existing Autofit Settings

Before populating content, note which boxes already have autofit enabled
vs. disabled — this affects your overflow strategy:

| Existing setting | Meaning | Your action |
|-----------------|---------|-------------|
| `<a:normAutofit/>` | Font will auto-shrink | Content can be slightly longer; still budget carefully |
| `<a:noAutofit/>` | Text gets clipped | Must stay within budget OR change to normAutofit |
| `<a:spAutoFit/>` | Box grows to fit text | Be careful — box may expand into other shapes |
| (missing)        | Default: usually clips | Treat as noAutofit; add normAutofit if needed |

---

## 7. Identify Invariant Brand Elements

Logos, background shapes, footer company names, watermarks — these live in the
slide master or layouts, not in slide XML. They inherit automatically.

Check what a slide inherits from its layout:
```bash
# Which layout does slide2 use?
cat /home/claude/unpacked/ppt/slides/_rels/slide2.xml.rels | grep slideLayout

# What's in that layout?
cat /home/claude/unpacked/ppt/slideLayouts/slideLayout2.xml | \
  grep -E 'type=|name=' | head -20
```

**Do not duplicate or override brand elements in slide XML.** They render
from the master/layout automatically.

---

## Analysis Checklist

Before moving to Step 2 (content planning):

- [ ] Layout inventory table completed for all template slides
- [ ] Visual thumbnails inspected — layout, colors, photo placement noted
- [ ] Color scheme slots recorded (accent1–6, dk1, dk2, lt1, lt2)
- [ ] Heading and body fonts noted
- [ ] Placeholder map filled for each slide to be used (idx, position, size)
- [ ] Autofit settings recorded for each content box
- [ ] Text box capacity estimated for every box that will receive content
- [ ] Invariant brand elements identified (logo, background, footer)
