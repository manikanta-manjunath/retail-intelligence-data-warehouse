---
title: Project Overview
category: project
status: current
last_updated: 2026-11-22
tags: [overview, retail, sql-server, streamlit]
---

# Project overview

Retail Intelligence is a Walmart-inspired educational platform that demonstrates a complete data-engineering and analytics workflow using SQL Server 2022, Python and Streamlit. All records currently loaded into the canonical warehouse are deterministic synthetic data, not Walmart internal data.

## Verified scope

- Sales and calendar coverage: **2010-01-01 through 2024-12-31**.
- Sales lines: **182,176** across **73,213** transactions.
- Reconciled net sales: **16,976,377.1400**.
- Inventory facts: **18,000**; shipment facts: **4,800**.
- Authenticated injected-anomaly labels: **1,607**.
- Repeat historical ETL: **zero** inserted facts and **zero** dimension updates.
- Automated suite: **25 passing tests**.

The machine-readable evidence is in [warehouse verification](../reports/generated/warehouse_verification.json) and the [analytics report](../reports/generated/analytics/analytics_report.json).

## Capabilities

1. Deterministic synthetic generation at four scales, including a non-overlapping historical mode.
2. Manifest and SHA-256 verification before parsing.
3. Typed business validation, rejection quarantine and immutable raw JSON archives.
4. Run-scoped staging, dimensional loading, SCD handling and atomic fact loading.
5. Grain, formula, reconciliation, referential-integrity and temporal verification.
6. Forecasting, basket rules, RFM clustering, anomaly evaluation, inventory classification, promotion analysis and supplier scorecards.
7. A filter-aware Streamlit dashboard with a dedicated problems and precision view.
8. Public-data adapters that preserve Walmart weekly and UCI invoice-line grains.

## Navigation

Continue with [Architecture](architecture.md), [ETL pipeline](etl-pipeline.md), [Analytics](analytics.md) or [Operations](operations.md).
