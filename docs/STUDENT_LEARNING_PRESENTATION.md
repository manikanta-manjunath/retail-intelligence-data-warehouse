---
marp: true
theme: default
paginate: true
title: Retail Intelligence — Self-Learning and Teamwork
description: Six-slide presentation for Data Mining and Data Warehousing
---

# 1. Retail Intelligence

## Self-Learning and Teamwork — DMDW

**15-Year Data Warehouse, Analytics and Dashboard**

**Manikanta M** · 1GA24CI069<br>
**Chinmay Gowda J** · 1GA24CI0XX<br>
B.E. CSE (AI & ML)

**Problem:** Retail data is distributed across sales, inventory, products, stores, customers, promotions and suppliers.

**Objective:** Build an audited 2010–2024 warehouse with repeatable ETL, analytical models and an interactive decision-support dashboard.

---

# 2. Architecture and Data Model

```text
CSV + Manifest → Validation → Raw Archive → Staging
        → Dimensions/Facts → Marts → Analytics → Dashboard
```

- **Schemas:** `raw`, `stg`, `dw`, `mart`, `audit`
- **Dimensions:** Date, Product, Store, Customer, Channel, Promotion, Supplier
- **Facts:** Sales line, inventory snapshot, shipment
- Product history uses **SCD Type 2**.
- Unique indexes, foreign keys and formula constraints protect quality.
- Repeat ETL inserted **zero duplicate facts**.

---

# 3. 48-Hour Learning and Teamwork

| Learning area | Hours |
| --- | ---: |
| Warehousing, dimensional design and OLAP | 18 |
| ETL, validation and data quality | 10 |
| Mining, clustering and anomaly analysis | 10 |
| Forecasting, dashboard and documentation | 10 |
| **Total** | **48** |

## Team practices

- Task allocation by architecture, ETL, analytics and presentation.
- Decisions recorded through GitHub and Markdown documentation.
- Tests and dashboard demonstrations used for peer review.

---

# 4. Analytics and Verified Results

| Result | Value |
| --- | ---: |
| Sales lines | 182,176 |
| Transactions | 73,213 |
| Reconciled net sales | 16,976,377.14 |
| Forecast backtest WAPE | 12.96% ± 3.63% |
| Unseen-test WAPE | 15.26% |
| Anomaly precision / recall | 12.48% / 62.24% |
| Detected review problems | 6,239 |
| Automated tests | 25 passed |

> Anomaly metrics apply only to injected synthetic high-quantity labels.

---

# 5. Dashboard and Decision Support

## Seven interactive views

- Executive KPIs and 15-year trend.
- Product and store performance.
- Filter-aware rolling-backtest forecast.
- Basket rules and RFM customer clusters.
- Inventory and supplier performance.
- Problems, precision and anomaly review.
- ETL audit history.

**Filters:** date, store, category and channel.

**Reliability:** short ranges show a clear 128-week requirement instead of an error.

---

# 6. Learning Outcomes and Future Work

## Key learning

- Correct grain and reconciliation are as important as model accuracy.
- Chronological evaluation prevents forecasting leakage.
- Synthetic results require transparent limitations.
- Documentation, testing and teamwork make analytics reproducible.

## Future work

- Integrate UCI and Kaggle sources into separate real-data marts.
- Add forecast confidence intervals and category-level anomaly models.
- Add GitHub Actions, authentication and secure deployment.

### Thank you

Repository documentation: [Project README](../README.md) · [Wiki](../wiki/index.md)
