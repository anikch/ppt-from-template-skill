# Content Mapping Reference

How to match topic content to template layouts, and how much content fits.

---

## Layout → Content Match Table

| Template Layout    | Ideal For                                 | Avoid                          |
|--------------------|-------------------------------------------|--------------------------------|
| Title Slide        | Presentation title, subtitle, date        | Long paragraphs                |
| Section Divider    | Section name, intro line (≤ 15 words)     | More than 2 text lines         |
| Title + Bullets    | Key findings, steps, features (≤ 5 items) | More than 6 bullets            |
| Two-Column         | Pros/cons, compare options, before/after  | Unequal content lengths        |
| Big Stat / Callout | Single KPI, bold claim, headline insight  | Multiple competing stats       |
| Image + Text       | Case study, product showcase, real example| Abstract concepts only         |
| Quote Slide        | Testimonial, executive quote, research    | Quotes over 25 words           |
| Timeline / Process | Steps, phases, roadmap                    | Non-sequential content         |
| Icon Grid          | Feature set, team members, service list   | Content needing heavy detail   |
| Closing / CTA      | Next steps, contact, thank you            | New content introductions      |

---

## Standard Presentation Structures

### Business Presentation (8–12 slides)
```
1.  Title Slide
2.  Agenda / Overview (3–5 bullets)
3.  Context / Problem
4–6. Key Findings (one per slide, varied layouts)
7.  Deep Dive on top finding
8.  Recommendations (3–5 action items)
9.  Key Metric Callout
10. Next Steps (owners + timelines)
11. Closing / Q&A
```

### Pitch Deck (10–15 slides)
```
1.  Title + Tagline
2.  The Problem
3.  The Solution
4.  How It Works
5.  Market Opportunity
6.  Business Model
7.  Traction / Proof
8.  Team
9.  Competition / Differentiation
10. Ask / CTA
```

### Educational / Training (6–10 slides)
```
1.  Title
2.  Learning Objectives
3.  Background / Context
4–6. Core Concepts (one per slide)
7.  Examples / Case Study
8.  Summary / Key Takeaways
9.  Discussion or Activity
10. Resources / Next Steps
```

### Status / Review Report (6–8 slides)
```
1. Title + Period
2. Executive Summary
3. Key Metrics / KPIs
4. Progress vs. Goals
5. Highlights (wins)
6. Risks / Issues
7. Next Period Priorities
```

---

## Content Density Rules

These rules exist to prevent overflow AND to maintain visual clarity.

**Titles:** Max 8 words / 40 characters. Make them specific:
- ✓ "Revenue Grew 40% in Q3" 
- ✗ "Financial Results"

**Bullets:** Max 5 per slide. Each bullet = 1 short phrase (≤ 12 words).
If you have 6+ points, split across two slides or group into categories.
Never write full sentences as bullets.

**Two-Column:** Keep both sides within 1 line of each other.
If content is heavily unequal, use a different layout.

**Stat Callouts:** One number per callout box. Always include units.
Stat label: ≤ 4 words. Supporting text: ≤ 20 words.

**Quotes:** ≤ 25 words. Always attribute: Name, Title, Organization.

**Body/description paragraphs:** ≤ 40 words per paragraph.
If a paragraph runs longer, split it or bullet it.

**Section dividers:** ≤ 2 lines total. These are breathing room slides.

---

## Slide Count by Request Type

| Type                   | Min | Typical | Max |
|------------------------|-----|---------|-----|
| Quick overview         | 4   | 6       | 8   |
| Standard business deck | 8   | 12      | 16  |
| Deep dive / workshop   | 12  | 20      | 30  |
| Pitch deck             | 8   | 12      | 15  |
| Status report          | 5   | 7       | 10  |

---

## Layout Sequencing Rules

- Never use the same layout for two consecutive content slides
- Always use a section divider between major topic shifts (every 3–4 slides)
- Put the most important stat/finding at slide 3 or 4 (peak attention zone)
- Closing slide should always be distinct — never same layout as content slides

---

## Working With User-Provided Context

If the user provides notes, a document, or a data file:
1. Extract 3–5 main themes → one content slide each
2. Pull statistics and facts → callout or metric slides
3. Identify natural sections → section divider slides
4. Spot quotes or testimonials → quote slide if layout exists
5. Find processes or steps → timeline/process slide if layout exists

If context is sparse, generate authoritative content on the topic using the
applicable structure above and note what assumptions were made.

---

## Template Constraint Scenarios

**Only 1–2 layouts available:**
Vary content density and visual weight between slides to avoid monotony.
Alternate between stat-heavy and text-heavy versions of the same layout.
Use section dividers to create visual breathing room.

**More layouts than content needs:**
Don't force every layout to be used. Choose the best fit. Unused layouts are fine.

**Template has placeholder images:**
Images cannot be injected programmatically in this environment. Options:
1. Keep existing placeholder images if they are thematically appropriate
2. Remove the `<p:pic>` element if the image distracts from the content
3. Tell the user which slides need real images swapped in manually afterward

**Template has very small text boxes (< 0.5" tall):**
These are typically labels, captions, or stat qualifiers — not body text areas.
Keep content to ≤ 6 words. If you need more space, expand `cy` in the XML.
