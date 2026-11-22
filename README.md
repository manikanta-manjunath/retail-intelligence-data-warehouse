# Retail Intelligence Data Warehouse

This is a Walmart-inspired educational retail intelligence system built on SQL Server 2022, Python and Streamlit. It demonstrates audited ingestion, a dimensional warehouse, repeatable ETL, OLAP queries, forecasting, market-basket analysis, RFM segmentation, anomaly detection, inventory analysis, supplier scorecards and a live dashboard.

The included canonical records are deterministic synthetic data. They are not Walmart internal data. Optional public-dataset adapters preserve source grain and do not invent transaction baskets, customers, costs or inventory.

## Verified state

The project was executed against SQL Server 2022 CU27 on 22 November 2026:

- Full calendar and sales coverage from 2010-01-01 through 2024-12-31 (15 years).
- 182,176 sales facts, 18,000 inventory snapshots and 4,800 shipments.
- 73,213 transactions and exact net sales of 16,976,377.1400.
- The historical extension accepted 242,809 source records with zero rejects.
- A second identical ETL run inserted zero facts and made zero dimension updates.
- Rolling-origin forecasting uses five backtest folds plus a final unseen 12-week test.
- Problem detection and precision/recall reporting use 1,607 authenticated synthetic labels.
- The complete automated suite passes 25/25 tests.

See [the verification report](docs/VERIFICATION_REPORT.md) for actual metrics and limits.

For topic-oriented, interlinked documentation, start with the [project wiki](wiki/index.md). It includes architecture, warehouse design, ETL, analytics, dashboard behavior, public datasets, operations, verification and roadmap pages.

## Student learning deliverables

- [Professional 30-page self-learning and teamwork report](docs/STUDENT_LEARNING_REPORT.md) — a detailed A4-ready academic report with 14,000+ words, verified preprocessing examples, ten Mermaid diagrams, technical results, teamwork, reflection and reproduction guidance.
- [Six-slide Markdown presentation](docs/STUDENT_LEARNING_PRESENTATION.md) — a Marp-compatible presentation covering the problem, architecture, learning process, results, dashboard and future work.

Before academic submission, complete all bracketed contribution, date and verification placeholders and attach only genuine personal, team and certificate evidence.

## Architecture

The system uses five SQL schemas:

- raw: current source-state tables plus immutable JSON row archives.
- stg: run-scoped, typed and validated records.
- dw: conformed dimensions, SCD history and atomic facts.
- mart: reporting and model-ready views.
- audit: ETL runs, manifests, rejected records and data-quality results.

Fact grains are explicit:

- dw.FactSales: one product line per transaction.
- dw.FactInventorySnapshot: one product, store and snapshot date.
- dw.FactShipment: one supplier shipment record.

Read [the architecture document](docs/ARCHITECTURE.md) for keys, history behavior and pipeline semantics.

## Requirements

- Python 3.11 or later.
- Docker with Compose.
- SQL Server container access on localhost:1433.
- About 1 GB for the Python environment and generated artifacts.

## Configuration

Copy the example and choose a strong local SQL Server password:

    cp .env.example .env

Set SQL_PASSWORD in .env. Do not commit .env. The password must match an existing container if one is already initialized; changing the Compose variable does not change a password stored inside an existing SQL Server volume.

Create a Python environment when the included local .venv is unavailable:

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt

Start SQL Server:

    docker compose up -d
    docker ps --filter name=retail_intelligence_dw

## Complete run

The setup command is non-destructive. It excludes reset, SCD demonstration and reporting-query scripts.

    .venv/bin/python -m src.cli setup

Generate a new declared synthetic dataset. Generation refuses to overwrite existing CSV files:

    .venv/bin/python -m src.cli generate --mode small --seed 42 --output data/synthetic/small_seed42

Generate the non-overlapping 2010–2022 historical extension used for the 15-year warehouse:

    .venv/bin/python -m src.cli generate --mode historical_15y --seed 42 --output data/synthetic/historical_2010_2022_seed42

Archive, validate, stage and load:

    .venv/bin/python -m src.cli etl --input data/synthetic/small_seed42

Verify keys, grain, formulas, reconciliation, history and analytical SQL:

    .venv/bin/python -m src.cli verify

Train and evaluate warehouse-backed analytics:

    .venv/bin/python -m src.cli analytics

Run the dashboard:

    .venv/bin/streamlit run dashboard/app.py

Open http://localhost:8501.

## Tests

Run the complete test suite, including local SQL Server integration:

    .venv/bin/python -m pytest -q tests

Run tests that do not require SQL Server:

    .venv/bin/python -m pytest -q tests -m "not integration"

## Public dataset adapters

The adapters preserve native source grain and write a manifest with input/output hashes.

### Recommended real datasets

1. [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) — recommended for this project. It contains about 1.07 million real invoice lines from December 2009 through December 2011 and is licensed under CC BY 4.0. Download `online_retail_II.xlsx`; the adapter imports every worksheet and preserves cancellations/returns.
2. [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail) — a smaller alternative with 541,909 invoice lines from December 2010 through December 2011, also CC BY 4.0. Download `Online Retail.xlsx`.
3. [Walmart Recruiting — Store Sales Forecasting](https://www.kaggle.com/competitions/walmart-recruiting-store-sales-forecasting/data) — weekly department sales for 45 stores, plus holidays, markdowns and economic features. Kaggle login and acceptance of the competition rules are required before downloading `train.csv`, `features.csv` and `stores.csv`.

Store downloaded files under `data/raw/public/` (ignored by Git). Do not commit the original datasets.

Normalize Walmart weekly store-department sales:

    .venv/bin/python -m src.cli adapt-public --dataset walmart-weekly --primary /path/to/train.csv --features /path/to/features.csv --stores /path/to/stores.csv --output data/processed/walmart-weekly

Normalize UCI Online Retail or Online Retail II:

    .venv/bin/python -m src.cli adapt-public --dataset uci-online-retail --primary /path/to/online_retail.xlsx --output data/processed/uci-online-retail

These commands normalize files only. Public data is not silently mixed into canonical facts because the Walmart dataset is weekly aggregate data while UCI is invoice-line data; neither contains all canonical inventory and supplier domains. Cite UCI when using its data and comply with Kaggle's competition rules.

## Safe operating rules

- Do not run sql/13_reset_demo_data.sql against data you need.
- sql/11_scd_type2_examples.sql rolls back its demonstration and is excluded from normal setup.
- Every model report contains a warehouse signature and limitations.
- Anomaly precision, recall and F1 apply only to injected high-quantity synthetic labels—not fraud or all real-world problems.
- Dashboard forecasts are rebuilt from the active date, store, category and channel filters and require at least 128 complete weeks.
- Promotion comparisons are descriptive and do not establish causality.
- Customer segmentation applies only to generated customer identifiers.

## Main outputs

- reports/generated/warehouse_verification.json
- reports/generated/etl_run_*.json
- reports/generated/analytics/analytics_report.json
- reports/generated/analytics/*.csv
- models/trained/*.joblib

Generated data and trained models are ignored by Git because they are reproducible. Reports remain available as evidence for this local project state.
