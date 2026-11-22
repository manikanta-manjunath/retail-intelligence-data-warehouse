# Self-Learning and Teamwork Report

## Data Mining & Data Warehousing — BCI24505D

**Project title:** Retail Intelligence Data Warehouse and Analytics Platform

**Submitted by:** `[Student Name]`

**USN:** `[University Seat Number]`

**Programme:** Bachelor of Engineering — Computer Science and Engineering (AI & ML)

**Institution:** Global Academy of Technology, Bengaluru

**Academic year:** 2026–2027
**Faculty guide:** Dr. Lokanna Kadakolmath, Associate Professor, Department of CSE (AI & ML)

> **Submission note:** Replace every bracketed placeholder, verify the dates and hours against your actual activity, and attach only genuine screenshots, certificates and team evidence before submitting this report.

---

## 1. Executive Summary

This report documents 48 hours of structured self-learning and collaborative work completed for Data Mining and Data Warehousing. The learning was applied through a retail intelligence case study implemented with SQL Server 2022, Python and Streamlit. The project covers a dimensional data warehouse, audited ETL, data-quality verification, OLAP-ready views, forecasting, association-rule mining, customer segmentation, anomaly analysis, inventory and supplier analytics, and an interactive dashboard.

The verified warehouse contains 15 years of calendar and sales coverage from 2010 through 2024, 182,176 sales lines, 73,213 transactions, 18,000 inventory snapshots and 4,800 shipment facts. The project also demonstrates repeatable ETL: replaying the historical input inserted zero duplicate facts. Forecast selection uses five rolling-origin backtests and an unseen test period, while anomaly precision and recall are reported only against authenticated synthetic injected labels.

The activity strengthened my understanding of dimensional modelling, fact grain, ETL reliability, preprocessing, clustering, association analysis, forecasting, anomaly evaluation, documentation and teamwork. It also taught me to distinguish technically correct outputs from defensible claims by documenting data provenance, limitations and reproducibility.

---

## 2. Purpose and Learning Objectives

The purpose of this activity was to transform classroom concepts into a reproducible analytics system that supports retail decision-making.

### Learning objectives

1. Understand the purpose and architecture of data warehouses and data marts.
2. Design fact and dimension tables using explicit business grains and surrogate keys.
3. Implement preprocessing, validation, staging, ETL auditing and source-to-target reconciliation.
4. Apply OLAP, association-rule mining, clustering, forecasting and anomaly detection.
5. Evaluate analytical results using appropriate metrics while preventing data leakage.
6. Develop professional teamwork, documentation, version-control and presentation skills.

### Course-outcome alignment

| Course outcome | Evidence from the project |
| --- | --- |
| C505D.1 — Data warehouse design and OLAP | Star-schema dimensions/facts, SCD Type 2 products, marts and OLAP SQL |
| C505D.2 — Preprocessing and similarity-ready data | Type/range validation, duplicate handling, reference checks, cancellation preservation and chronological splits |
| C505D.3 — Classification/association techniques | FP-Growth basket rules and labelled anomaly evaluation using precision, recall and F1 |
| C505D.4 — Clustering | K-means RFM customer segmentation with silhouette evaluation |

---

## 3. Summary of Hours

| Activity category | Hours | Evidence |
| --- | ---: | --- |
| Individual self-learning and hands-on implementation | 36 | Source code, SQL scripts, configuration, tests, generated reports and learning notes |
| Teamwork and collaborative review | 12 | Task discussions, repository history, review feedback, dashboard validation and presentation preparation |
| **Total** | **48** | Must match the verified activity record |

---

## 4. 48-Hour Activity Log

| Week | Date | Topic | Hours | Learning and practical activities | Evidence |
| ---: | --- | --- | ---: | --- | --- |
| 1 | 07-09-2026 to 12-09-2026 | Introduction to Data Warehousing | 6 | Studied operational versus analytical systems, warehouse characteristics, dimensional modelling, fact grain and surrogate keys. Analysed the retail problem and identified sales, inventory and shipment processes. | [Architecture wiki](../wiki/architecture.md), [project overview](../wiki/overview.md) |
| 2 | 14-09-2026 to 19-09-2026 | Data Warehouse Design | 6 | Designed seven conformed dimensions and three atomic facts. Reviewed SCD Type 1 and Type 2 behavior, business-key uniqueness, referential integrity and measure constraints. | [Data-model wiki](../wiki/data-model.md), [dimension SQL](../sql/03_create_dimensions.sql), [fact SQL](../sql/04_create_fact_tables.sql) |
| 3 | 21-09-2026 to 26-09-2026 | ETL Process | 6 | Implemented manifest/hash verification, typed validation, rejection quarantine, immutable source archives, run-scoped staging, incremental loading and exact reconciliation. Tested idempotent replay. | [ETL wiki](../wiki/etl-pipeline.md), [pipeline](../src/etl/pipeline.py), [validation](../src/etl/validation.py) |
| 4 | 28-09-2026 to 03-10-2026 | OLAP Operations | 6 | Practised roll-up, drill-down, slice, dice and ranking queries. Created executive, product, store, inventory, supplier and customer marts for decision support. | [OLAP examples](../sql/09_olap_examples.sql), [reporting queries](../sql/12_reporting_queries.sql) |
| 5 | 05-10-2026 to 10-10-2026 | Introduction to Data Mining | 6 | Studied the KDD process, feature preparation, supervised versus unsupervised learning, leakage prevention and metric selection. Connected mining tasks to retail decisions. | [Analytics wiki](../wiki/analytics.md), [analytics runner](../src/analytics/run.py) |
| 6 | 12-10-2026 to 17-10-2026 | Association Rule Mining | 6 | Built transaction baskets, applied FP-Growth, interpreted support, confidence and lift, and documented that generated affinities limit external validity. | [Mining implementation](../src/analytics/mining.py), [association rules](../reports/generated/analytics/association_rules.csv) |
| 7 | 19-10-2026 to 24-10-2026 | Classification and Clustering | 6 | Applied K-means to RFM features, evaluated clusters with silhouette score, trained an Isolation Forest chronologically, and calculated precision, recall, F1 and confusion counts against injected labels. | [Mining implementation](../src/analytics/mining.py), [analytics report](../reports/generated/analytics/analytics_report.json) |
| 8 | 16-11-2026 to 21-11-2026 | Mini Project / Case Study | 6 | Integrated the 15-year warehouse, rolling-origin forecasting, problem detection and Streamlit dashboard. Completed testing, documentation, GitHub review and presentation preparation. | [Dashboard](../dashboard/app.py), [verification report](VERIFICATION_REPORT.md), [project wiki](../wiki/index.md) |

---

## 5. Teamwork and Contribution

### Team objective

The team objective was to develop a reliable retail intelligence platform that converts raw sales, inventory and supplier records into an audited warehouse, analytical models and an understandable dashboard.

### My role and responsibilities

- Studied the retail domain and translated business events into fact-table grains.
- Contributed to the data model, SQL objects and ETL workflow.
- Validated source data, reconciliation logic and repeatability.
- Implemented or reviewed forecasting, clustering, basket analysis and anomaly metrics.
- Tested dashboard filters and documented limitations.
- Maintained GitHub commits, pull-request documentation and the project wiki.

### Coordination and communication

Work was divided into data modelling, ETL, analytics, dashboard and documentation tasks. Progress was reviewed using shared repository changes, test results and dashboard demonstrations. Decisions were recorded in Markdown documentation so that implementation details remained understandable to all members.

### Handling decisions or disagreements

When choosing between replacing the existing warehouse and appending historical records, the team selected a non-destructive approach. Historical business keys received safe prefixes, existing 2023–2024 facts were preserved, and the combined result was verified as a continuous 2010–2024 dataset. This decision reduced risk and made repeatability measurable.

### Contribution of other team members

`[Add each team member's name and factual contribution here. Do not assign work that the person did not perform.]`

### Outcome of teamwork

The team produced a working warehouse and dashboard, 25 passing automated tests, exact source reconciliation, repeatable ETL, model evaluation reports, professional documentation and a reviewable GitHub pull request.

---

## 6. Case Study Understanding and Domain Exploration

### Case-study title and domain

**Retail Intelligence Data Warehouse and Analytics Platform — Retail and Business Intelligence**

### Problem statement

Retail organizations generate sales, product, store, customer, promotion, inventory and supplier data at different grains. Without a conformed warehouse, decision-makers cannot reliably compare long-term performance, trace data-quality problems, evaluate forecasts or identify operational risks. The case study addresses this by creating a governed analytical platform with explicit provenance and repeatability.

### Objectives and scope

1. Build a 15-year warehouse for sales analysis without deleting existing records.
2. Enforce atomic grains, dimensional integrity and financial formulas.
3. Provide exact source-to-target reconciliation and idempotent reruns.
4. Apply forecasting, clustering, basket mining and anomaly evaluation.
5. Detect actionable sales, discount, inventory, supplier and ETL problems.
6. Present filtered results through an interactive dashboard.

### Stakeholders

- Retail executives: revenue, profit and trend monitoring.
- Store and category managers: product/store performance and discount review.
- Inventory teams: stockout and understock monitoring.
- Procurement teams: supplier delay and partial-fill analysis.
- Data engineers and auditors: lineage, quality checks and ETL history.
- Data analysts: reproducible model-ready datasets and evaluation outputs.

### Expected analytical value

The platform supports long-term comparison, filtered forecasts, product affinity analysis, customer segmentation, anomaly review, inventory prioritization and supplier performance assessment. It also makes uncertainty and limitations visible instead of presenting model outputs as unquestionable facts.

---

## 7. Dataset Study and Data Preprocessing

### Dataset description and source

The verified canonical warehouse uses deterministic synthetic retail data generated by the project. It is explicitly labelled `SYNTHETIC_CANONICAL` and is not Walmart proprietary data. The combined dataset covers 2010–2024.

Official real-data options are documented for future analysis:

- [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) — invoice-line transactions, CC BY 4.0.
- [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail) — smaller invoice-line dataset, CC BY 4.0.
- [Kaggle Walmart Recruiting — Store Sales Forecasting](https://www.kaggle.com/competitions/walmart-recruiting-store-sales-forecasting/data) — weekly store-department data subject to competition rules.

### Important attributes

| Domain | Key attributes | Role |
| --- | --- | --- |
| Sales | TransactionID, line number, date, product, store, customer, channel | Atomic transaction-line grain |
| Measures | Quantity, unit price, discount, net sales, cost, profit | Financial and demand analysis |
| Product | Category, subcategory, brand, supplier, cost, price | Product dimension and SCD history |
| Inventory | Snapshot date, product, store, on-hand, reorder point | Stock health and replenishment risk |
| Shipment | Supplier, order/promised/actual dates, ordered/received quantities | Delay and fill-rate analysis |

### Data-quality assessment and preprocessing

- Verified SHA-256 hashes and expected row counts before parsing.
- Parsed dates, times, integers and bounded decimal values.
- Enforced business-key uniqueness and quarantined conflicting duplicates.
- Rejected unresolved product/store/customer references.
- Quarantined complete sales baskets when a dependent line was invalid.
- Preserved cancellations and negative quantities in public UCI adapters where meaningful.
- Completed missing calendar days and zero-filled sales before weekly aggregation.
- Used chronological splits to prevent future data from entering model training.

### Before/after summary

| Item | Before validation | After loading | Notes |
| --- | ---: | ---: | --- |
| Historical source records | 242,809 | 242,809 accepted | Zero rejected in the verified historical run |
| Sales lines | 160,057 historical extension | 182,176 combined facts | Existing 22,119 lines were preserved |
| Duplicate fact grains | Not assumed | 0 | Verified through warehouse checks |
| Raw/fact net-sales difference | Not assumed | 0.0000 | Exact reconciliation |
| Calendar gaps | Not assumed | 0 | Continuous 2010–2024 dimension |

Reproducibility is controlled by seed 42, configuration files, file hashes, warehouse signatures and versioned source code.

---

## 8. Data Warehouse and ETL Implementation

The warehouse uses `raw`, `stg`, `dw`, `mart` and `audit` schemas. Seven dimensions conform dates, products, stores, customers, channels, promotions and suppliers. Three fact tables store sales lines, inventory positions and shipments.

Product changes use SCD Type 2. Store, customer, promotion and supplier corrections use Type 1 behavior where appropriate. An application lock serializes warehouse writers, while `XACT_ABORT` and transaction rollback protect atomicity.

The ETL workflow authenticates manifests, validates data, archives every original row as JSON, stages accepted records, synchronizes source-state tables, loads dimensions/facts, inserts synthetic labels, reconciles counts and amounts, and completes the audit run. Replaying the same historical batch inserted zero facts and made zero updates.

See the [architecture](../wiki/architecture.md), [data model](../wiki/data-model.md) and [ETL pipeline](../wiki/etl-pipeline.md).

---

## 9. Data Mining and Analytical Implementation

### Association-rule mining

FP-Growth evaluated 73,213 transaction baskets using minimum support, confidence and lift thresholds. Five rules passed the verified configuration. Because some affinities were embedded by the generator, these rules demonstrate the method rather than independent real-world discovery.

### Customer clustering

K-means clustered 500 generated customers using log-transformed and standardized RFM features. Four clusters produced a silhouette score of approximately **0.273**. Cluster profiles support descriptive customer comparison but are not a classification target.

### Forecasting

Weekly sales forecasting compared naive, moving-average, exponential-smoothing, random-forest and gradient-boosting models. Selection used five expanding-window rolling-origin folds; the final 12 weeks remained unseen. Exponential smoothing achieved:

| Metric | Result |
| --- | ---: |
| Mean backtest WAPE | 12.96% |
| Backtest WAPE standard deviation | 3.63% |
| Unseen-test WAPE | 15.26% |
| Unseen-test MASE | 0.62 |

### Anomaly evaluation

Isolation Forest was trained on the chronological first 80% of sales lines, excluding labelled injected anomalies. In the evaluation period it produced:

| Metric | Result |
| --- | ---: |
| Evaluated lines | 36,241 |
| Injected positive lines | 143 |
| Flagged lines | 713 |
| Precision | 12.48% |
| Recall | 62.24% |
| F1-score | 0.208 |

These metrics apply only to injected high-quantity anomalies, not fraud detection.

### Problem detection

The project generated 6,239 review records covering excessive discounts, stockouts, understock, supplier delays, partial fills, sales spikes and year-over-year decline.

---

## 10. Results and Interpretation

The project achieved exact data reconciliation, continuous date coverage and repeatable loading. The dashboard correctly recalculates filtered KPIs and forecasts using selected dates, stores, categories and channels. Short selections display a clear 128-week minimum-history message instead of failing.

The strongest result is not a single model score; it is the combination of data lineage, validation, reproducibility and honest evaluation. Forecast WAPE indicates useful demonstration performance, while anomaly precision shows that statistical outliers require human review. The low precision also highlights the difference between synthetic labels and the broader concept of operational anomalies.

All 25 automated tests passed, including SQL integration, idempotency, SCD behavior, public-data adaptation, model evaluation and Streamlit execution.

---

## 11. Overall Reflection and Conclusion

Completing the 48-hour activity significantly improved my ability to connect data-mining theory with an end-to-end engineering system. Initially, I viewed a data warehouse mainly as a collection of fact and dimension tables. Through implementation, I learned that grain definition, source authentication, referential integrity, historical handling and reconciliation are equally important. Building the ETL pipeline strengthened my practical understanding of validation, staging, idempotency and auditability.

The analytical work also changed how I interpret model results. I learned to use chronological evaluation for forecasting, silhouette score for clustering, and precision, recall and F1 for labelled anomaly evaluation. More importantly, I learned to state limitations clearly when data is synthetic or labels represent only one anomaly type. Teamwork improved my communication, task planning, code-review and documentation skills. Using GitHub and an interlinked project wiki made decisions and evidence easier to review.

In future, I would integrate UCI and Kaggle data into separate source-specific marts, add confidence intervals, improve category-level anomaly models, implement GitHub Actions and deploy a secure demonstration. Overall, the activity developed independent learning, practical problem-solving and professional responsibility.

---

## 12. Evidence and Reproducibility

### Repository evidence

- [README](../README.md)
- [Project wiki](../wiki/index.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Verification report](VERIFICATION_REPORT.md)
- [Analytics report](../reports/generated/analytics/analytics_report.json)
- [Automated tests](../tests/)
- [Dashboard source](../dashboard/app.py)

### Evidence to attach before submission

- `[Screenshot: dashboard executive view]`
- `[Screenshot: forecast and metrics]`
- `[Screenshot: problems and precision tab]`
- `[Screenshot: SQL warehouse tables or verification output]`
- `[Screenshot: GitHub repository and pull request]`
- `[Team meeting record / task-allocation evidence]`
- `[Only genuine certificates or course-completion evidence]`

### Reproduction commands

```bash
docker compose up -d
.venv/bin/python -m src.cli setup
.venv/bin/python -m src.cli verify
.venv/bin/python -m src.cli analytics
.venv/bin/python -m pytest -q
./run_dashboard.sh
```

---

## 13. Declaration and Verification

I declare that this report accurately represents the self-learning and teamwork activities completed by me. I have verified the recorded hours and have included only evidence that can be authenticated. I understand that all synthetic and public datasets must be described with their correct provenance and limitations.

| Student | Faculty verification |
| --- | --- |
| **Name:** `[Student Name]` | **Remarks:** `[Faculty Remarks]` |
| **USN:** `[USN]` | **Faculty signature:** ____________________ |
| **Signature:** ____________________ | **Date:** `[DD/MM/YYYY]` |
| **Date:** `[DD/MM/YYYY]` |  |
