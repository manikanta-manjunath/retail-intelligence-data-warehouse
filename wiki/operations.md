---
title: Operations Guide
category: operations
status: current
last_updated: 2026-11-22
tags: [setup, commands, docker, recovery]
---

# Operations guide

## Prerequisites

- Python 3.11 or later.
- Docker with Compose.
- Approximately 1 GB for the Python environment and generated artifacts.
- A strong local SQL Server `sa` password stored in `.env`.

## Initial setup

```bash
cp .env.example .env
# Edit SQL_PASSWORD in .env before starting SQL Server.

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
docker compose up -d
.venv/bin/python -m src.cli setup
```

Setup is non-destructive and uses an explicit SQL allowlist.

## Standard workflow

```bash
.venv/bin/python -m src.cli status
.venv/bin/python -m src.cli generate --mode small --seed 42 \
  --output data/synthetic/small_seed42
.venv/bin/python -m src.cli etl --input data/synthetic/small_seed42
.venv/bin/python -m src.cli verify
.venv/bin/python -m src.cli analytics
./run_dashboard.sh
```

Generation refuses to overwrite existing CSV directories. Choose a new output directory or intentionally archive the old one.

## Safe operating rules

- Do not execute `sql/13_reset_demo_data.sql` against data that must be preserved.
- `sql/11_scd_type2_examples.sql` is a rolled-back demonstration and is excluded from setup.
- Do not commit `.env`, downloaded datasets, generated canonical data or trained model files.
- Treat `reports/generated/` as evidence tied to the warehouse signature in `analytics_report.json`.
- Run verification before analytics and before presenting results.

## Failure recovery

1. Read the most recent row in `mart.vw_ETLRunSummary`.
2. Inspect `audit.RejectedRecord`, `audit.DataQualityLog` and the corresponding immutable `raw.IngestedRecord` archive.
3. Correct the source or code; do not manually patch facts to bypass reconciliation.
4. Re-run the same input. Idempotent keys prevent duplicate facts.

## Dashboard availability

`run_dashboard.sh` checks the environment, SQL Server and warehouse state before starting Streamlit. The live URL is [http://localhost:8501](http://localhost:8501).

## Source references

- [CLI](../src/cli.py)
- [Database executor](../src/db/executor.py)
- [Dashboard runner](../run_dashboard.sh)
