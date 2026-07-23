---
name: office-pandoc
description: >
  Create or convert Word/PDF/slides with pandoc and lightweight Python —
  reports, memos, simple decks — without relying on product Office skill
  scripts. Triggers: pandoc docx, make a report pdf, simple slides from
  markdown, /office-pandoc.
version: 1.0.0
author: luckyseoul
license: MIT
---

# Office via Pandoc

## Prefer when
- Markdown → `.docx` / `.pdf` / reveal.js or beamer
- User does not need pixel-perfect PowerPoint template editing

## Prefer product `/docx` or `/pptx` when
- Complex template fill, thumbnail QA, or advanced layout

## Recipes
```bash
# Markdown report → Word
pandoc report.md -o report.docx --reference-doc=optional-ref.docx

# Markdown → PDF (if pdflatex/weasyprint available)
pandoc report.md -o report.pdf

# Simple slides from markdown
pandoc slides.md -t revealjs -s -o slides.html
```

## Quality bar
- Complete sentences, real headings, no placeholder lorem.
- Cite sources when research-derived.
