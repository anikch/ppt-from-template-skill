# Multi-Template Reference

How to work with multiple `.pptx` files uploaded to the same session.

---

## When This Applies

The user has uploaded 2+ `.pptx` files representing:
- Different slide styles from the same brand library
- A master template plus a supplementary slide pack
- Multiple versions of the same template (choose the best one)
- Slides from different sources to be combined into one deck

---

## Step 1 — Inventory All Templates

```bash
ls /mnt/user-data/uploads/*.pptx
```

For each file, run the full analysis pipeline:
```bash
python -m markitdown /mnt/user-data/uploads/template-A.pptx
python /mnt/skills/public/pptx/scripts/thumbnail.py \
  /mnt/user-data/uploads/template-A.pptx /home/claude/thumbs-A

python -m markitdown /mnt/user-data/uploads/template-B.pptx
python /mnt/skills/public/pptx/scripts/thumbnail.py \
  /mnt/user-data/uploads/template-B.pptx /home/claude/thumbs-B
```

Build a combined layout inventory table covering all files.

---

## Step 2 — Choose a Primary Template

Pick the template with:
- The most layout variety
- The strongest brand completeness (logo, colors, fonts in place)
- The best fit for the presentation's purpose

```bash
cp /mnt/user-data/uploads/template-A.pptx /home/claude/template.pptx
python /mnt/skills/public/pptx/scripts/office/unpack.py \
  /home/claude/template.pptx /home/claude/unpacked/
```

---

## Step 3 — Import a Layout from a Secondary Template

Only needed when the secondary template has a layout (e.g., a timeline, icon
grid) that the primary lacks and the content genuinely requires.

### 3a — Unpack secondary template

```bash
python /mnt/skills/public/pptx/scripts/office/unpack.py \
  /mnt/user-data/uploads/template-B.pptx /home/claude/unpacked-B/
```

### 3b — Copy slide XML and its relationships

```bash
cp /home/claude/unpacked-B/ppt/slides/slide5.xml \
   /home/claude/unpacked/ppt/slides/slide_imported.xml

cp /home/claude/unpacked-B/ppt/slides/_rels/slide5.xml.rels \
   /home/claude/unpacked/ppt/slides/_rels/slide_imported.xml.rels
```

### 3c — Copy referenced media files

Check what media the slide uses:
```bash
cat /home/claude/unpacked-B/ppt/slides/_rels/slide5.xml.rels
```

Copy referenced images with renamed filenames to avoid conflicts:
```bash
cp /home/claude/unpacked-B/ppt/media/image3.png \
   /home/claude/unpacked/ppt/media/image3_imported.png
```

Update the `.rels` file to reference the new media filenames.

### 3d — Register in [Content_Types].xml

Add to `/home/claude/unpacked/[Content_Types].xml`:
```xml
<Override PartName="/ppt/slides/slide_imported.xml"
  ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
```

### 3e — Register in presentation relationships

Add to `ppt/_rels/presentation.xml.rels`:
```xml
<Relationship Id="rIdNEW"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
  Target="slides/slide_imported.xml"/>
```

Add to `<p:sldIdLst>` in `ppt/presentation.xml` (use id higher than current max):
```xml
<p:sldId id="UNIQUE_ID" r:id="rIdNEW"/>
```

### 3f — Resolve layout references

The imported slide references a `slideLayout` from template B. Choose:

**Option A — Remap to closest primary layout (simpler):**
Edit the imported slide's `.rels` file to point `rId1` (or whichever rId
points to slideLayout) at the closest matching layout in the primary template.

```bash
# Find the layout file used by the imported slide
grep slideLayout /home/claude/unpacked/ppt/slides/_rels/slide_imported.xml.rels

# List primary template layouts to find the closest match
ls /home/claude/unpacked/ppt/slideLayouts/
```

**Option B — Copy the layout from template B (complete fidelity):**
Follow the same copy/register process as above but for `ppt/slideLayouts/`
and `ppt/slideLayouts/_rels/`. Also copy any referenced slide masters.

Option A is usually sufficient. Use Option B only when the imported slide
has a highly specific layout that doesn't map to any primary template layout.

---

## Step 4 — Verify the Merge

```bash
# Clean up references
python /mnt/skills/public/pptx/scripts/clean.py /home/claude/unpacked/

# Pack
python /mnt/skills/public/pptx/scripts/office/pack.py \
  /home/claude/unpacked/ /home/claude/template-merged.pptx \
  --original /home/claude/template.pptx

# Render to images
python /mnt/skills/public/pptx/scripts/office/soffice.py \
  --headless --convert-to pdf /home/claude/template-merged.pptx
pdftoppm -jpeg -r 150 /home/claude/template-merged.pdf slide-merged
```

Inspect every slide image, paying particular attention to:
- Imported slides rendering with correct fonts and colors (not generic fallbacks)
- No missing images (broken image icons indicate unresolved media references)
- Brand consistency — imported slides should feel visually compatible

---

## Step 5 — Run Full QA on the Merged Deck

```bash
python /mnt/skills/user/generating-pptx-from-template/scripts/check_placeholders.py \
  /home/claude/template-merged.pptx

python /mnt/skills/user/generating-pptx-from-template/scripts/audit_overflow.py \
  /home/claude/unpacked/ppt/slides/
```

Fix all issues before delivering.

---

## Simpler Alternative: Deliver as Separate Files

If merging is complex or risky, generate each section from its own template
independently and deliver two `.pptx` files. Tell the user:

> "These two files can be combined in PowerPoint via **Insert → Reuse Slides**,
> or by dragging slides from one open presentation into another."

---

## When Templates Are Near-Identical

If the uploaded files are clearly the same brand template in different states
(e.g., empty vs. partially filled, or two color variants), use the cleanest
and most complete one. No merge needed — just pick the best source.
