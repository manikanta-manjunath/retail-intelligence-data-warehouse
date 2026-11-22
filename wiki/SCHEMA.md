---
title: Wiki Schema and Maintenance Rules
category: governance
status: current
last_updated: 2026-11-22
tags: [wiki, governance, documentation]
---

# Wiki schema and maintenance rules

## Layer ownership

1. **Raw evidence**: files under `src/`, `sql/`, `config/`, `tests/`, `reports/generated/` and official external dataset pages. These are read as evidence and are not rewritten merely to make wiki prose consistent.
2. **Wiki**: Markdown files under `wiki/`. These synthesize evidence and may be updated whenever code, results or understanding changes.
3. **Canonical project documentation**: `README.md`, `docs/ARCHITECTURE.md`, `docs/VERIFICATION_REPORT.md` and `LICENSES_AND_DATA_SOURCES.md`. Material wiki discoveries must be reflected here when they affect setup, architecture, verified results or licensing.

## Page format

Every page must contain YAML frontmatter with:

- `title`
- `category`
- `status`: `current`, `draft`, `superseded` or `needs-review`
- `last_updated`: ISO date
- `tags`

Pages should include links to related wiki pages and direct links to the most important source files. Claims about counts, accuracy or successful execution must point to generated evidence or tests.

## Update workflow

### Ingest

1. Identify the new or changed source.
2. Read the current [index](index.md) and related pages.
3. Update every affected page rather than adding an isolated summary.
4. Reconcile contradictions. Preserve both claims if evidence is unresolved and mark the page `needs-review`.
5. Update `index.md` for new pages.
6. Append an entry to [log.md](log.md).

### Query

Read `index.md`, then the smallest relevant set of pages and their cited sources. If the answer produces reusable analysis, file it into the most relevant page or add a new linked page.

### Lint

Check for broken relative links, pages absent from the index, stale counts, unsupported accuracy claims, missing external-license notes, duplicated explanations and claims contradicted by newer generated reports.

## Naming and linking

- Use lowercase kebab-case filenames.
- Prefer standard relative Markdown links so the wiki works in GitHub and Obsidian.
- Use one page per durable concept; avoid one page per source file.
- Do not copy secrets, `.env` values, raw customer-like records or proprietary content into the wiki.

