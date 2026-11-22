---
title: ETL Pipeline
category: data-engineering
status: current
last_updated: 2026-11-22
tags: [etl, validation, audit, idempotency]
---

# ETL pipeline

## Input contract

A canonical directory contains ten CSV files and `manifest.json`. The manifest declares the source system, synthetic status, seed, generation range, per-file row counts and SHA-256 hashes. Historical generation can also declare `ground_truth_sales_anomalies.csv` with its own hash and count.

The loader accepts declared `SYNTHETIC_CANONICAL` input only. Public adapters write separate source-specific outputs and do not silently enter canonical facts.

## Processing stages

1. **Authenticate input**: verify source-system declaration, file hashes and manifest row counts.
2. **Validate**: parse types, enforce decimals/ranges, resolve references, detect duplicate keys and quarantine invalid baskets/dependents.
3. **Start audit run**: create an `ETLRunHistory` row and persist the input manifest.
4. **Archive originals**: serialize every source row to immutable JSON with a record hash, including rows later rejected.
5. **Stage accepted records**: insert typed rows under one `ETLRunID`.
6. **Synchronize current source state**: update mutable dimensions, reject conflicting immutable records and insert new keys.
7. **Load warehouse**: run five dimension procedures and three fact procedures.
8. **Load ground truth**: validate anomaly transaction-line keys and insert labels idempotently.
9. **Reconcile**: compare accepted sales counts and amounts plus inventory/shipment keys against facts.
10. **Commit and report**: persist quality results, complete the audit run and write a JSON run report.

## Failure behavior

The warehouse transaction uses `XACT_ABORT` and rolls back on exceptions. The run is marked `FAILED` with a bounded error message. Original-row archives are intentionally retained for diagnosis.

## Repeatability evidence

Historical run 16 accepted 242,809 records and inserted 160,057 sales, 9,000 inventory and 4,000 shipment facts. Replaying the same input in run 17 inserted zero facts and updated zero dimensions.

## Commands

```bash
.venv/bin/python -m src.cli setup
.venv/bin/python -m src.cli generate --mode historical_15y --seed 42 \
  --output data/synthetic/historical_2010_2022_seed42
.venv/bin/python -m src.cli etl \
  --input data/synthetic/historical_2010_2022_seed42
.venv/bin/python -m src.cli verify
```

## Source references

- [Generator](../src/ingestion/generator.py)
- [Validation](../src/etl/validation.py)
- [Pipeline](../src/etl/pipeline.py)
- [ETL procedures](../sql/06_create_etl_procedures.sql)
- [Verification](../src/etl/verify.py)

