# Generating PPTX from Template — Claude Skill

A Claude AI skill that produces polished PowerPoint presentations using an uploaded `.pptx` file as the design source of truth. The output inherits the template's exact visual identity — colors, fonts, layouts, logos, and branding — with no generic AI aesthetics or hardcoded overrides.

## What This Does

When you upload a `.pptx` template to Claude and ask it to create a presentation, this skill ensures:

- **Brand fidelity**: Colors, fonts, and layouts come from your template's theme — not hardcoded values
- **Overflow prevention**: Text boxes are measured before content is written, with automated auditing to catch overflow before delivery
- **Layout variety**: Content is mapped to the best-fitting layout, with no two consecutive slides using the same structure
- **QA pipeline**: Placeholder detection, visual rendering, and overflow auditing run automatically before final output

## Repository Structure

```
├── SKILL.md                          # Main skill instructions (the "brain")
├── LICENSE                           # MIT License
├── references/
│   ├── template-analysis.md          # How to inspect templates: colors, fonts, placeholders
│   ├── content-editing.md            # XML patterns + full text overflow fix protocol
│   ├── content-mapping.md            # Layout-to-content matching and density rules
│   └── multi-template.md             # Merging multiple uploaded templates
└── scripts/
    ├── audit_overflow.py             # Automated overflow detection per text box
    └── check_placeholders.py         # QA gate for leftover placeholder text
```

## How to Use as a Claude Skill

1. In Claude's settings, add this as a custom skill
2. Upload any `.pptx` template file in your conversation
3. Ask Claude to create a presentation on your topic
4. Claude will analyze your template, plan content to fit the layouts, and deliver a branded deck

## Key Features

### Overflow Prevention
The skill measures every text box's dimensions and font size before writing content, applying an 80% capacity budget. The `audit_overflow.py` script catches issues automatically:

```bash
python scripts/audit_overflow.py /path/to/unpacked/ppt/slides/
```

Reports each text box as:
- 🔴 **OVERFLOW** — must fix before delivering
- 🟡 **AT RISK** — review visually

### Placeholder Detection
The `check_placeholders.py` script catches leftover template text:

```bash
python scripts/check_placeholders.py output.pptx
python scripts/check_placeholders.py output.pptx --strict  # also catches demo names, example URLs
```

### Multi-Template Support
When multiple `.pptx` files are uploaded, the skill selects the richest template as primary and can import specific layouts from secondary templates.

## Dependencies

```bash
pip install "markitdown[pptx]" Pillow defusedxml
apt-get install poppler-utils  # for PDF-to-image rendering during QA
```

## License

MIT — use it, modify it, share it, sell it, do whatever you want. See [LICENSE](LICENSE) for details.
