---
title: System Architecture
category: architecture
status: current
last_updated: 2026-11-22
tags: [architecture, sql-server, python, streamlit]
---

# System architecture

## End-to-end flow

```text
Canonical CSVs + manifest
        │
        ▼
Hash verification and typed validation
        │
        ├── rejected rows ──► audit.RejectedRecord
        ▼
raw.IngestedRecord immutable JSON archive
        │
        ▼
Run-scoped stg tables ──► current raw source tables
        │
        ▼
Conformed dimensions and atomic facts
        │
        ▼
dw/mart reporting views
        │
        ├──► Python analytics + model artifacts
        └──► Streamlit dashboard
```

## SQL schemas

| Schema | Responsibility |
| --- | --- |
| `raw` | Current accepted source state and immutable original-row archives |
| `stg` | Typed records isolated by `ETLRunID` |
| `dw` | Conformed dimensions, SCD history and atomic facts |
| `mart` | Business summaries and model-ready views |
| `audit` | Runs, manifests, rejections, quality checks and synthetic labels |

## Python packages

| Package | Responsibility |
| --- | --- |
| `src.ingestion` | Synthetic generation and public-source normalization |
| `src.etl` | Validation, loading, reconciliation and verification |
| `src.analytics` | Warehouse querying, models, problem detection and reports |
| `src.db` | SQL Server connectivity and setup-script execution |
| `src.utils` | Configuration and logging |
| `dashboard` | Interactive presentation and filtered analysis |

## Reliability boundaries

- An SQL application lock serializes warehouse writers.
- Source archives remain observable even when the warehouse transaction fails.
- Staging, source synchronization, dimensions, facts, quality results and successful completion commit together.
- Immutable fact-key conflicts abort instead of silently replacing history.
- Setup uses an explicit script allowlist and excludes the destructive reset and demonstration scripts.

For detailed grains and keys, see [Warehouse data model](data-model.md). For transaction behavior, see [ETL pipeline](etl-pipeline.md).

## Source references

- [SQL setup order](../src/db/executor.py)
- [ETL implementation](../src/etl/pipeline.py)
- [Canonical architecture document](../docs/ARCHITECTURE.md)
