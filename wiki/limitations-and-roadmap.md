---
title: Limitations and Roadmap
category: roadmap
status: current
last_updated: 2026-11-22
tags: [limitations, roadmap, future-work]
---

# Limitations and roadmap

## Current limitations

### Data validity

- The canonical warehouse contains synthetic educational records.
- Embedded basket affinities make association-rule findings unsuitable as independent evidence.
- Inventory covers 30 SKUs across five stores for 60 days in each generated load.
- Public data is normalized but not yet conformed into the canonical star schema.

### Analytics

- Forecast accuracy is estimated on generated behavior and does not guarantee real-world performance.
- Injected labels represent only high-quantity anomalies; precision and recall do not measure fraud.
- Promotion analysis is descriptive and does not establish causal lift.
- RFM clusters are descriptive and use generated customer identifiers.

### Platform

- No role-based access control or authentication.
- No production scheduler, orchestration service or alert delivery.
- No returns fact, inventory-movement ledger or complete purchase-order lifecycle.
- No automated GitHub Actions workflow is currently reported on the feature branch.

## Recommended roadmap

1. **Real-data analysis layer**: load UCI invoice lines and Walmart weekly aggregates into separate source-specific marts.
2. **CI/CD**: run tests, compilation and SQL lint checks on every pull request.
3. **Forecast uncertainty**: add prediction intervals and segment-level backtests.
4. **Anomaly specialization**: train per-category or per-product models and calibrate review thresholds.
5. **Exports**: allow filtered CSV downloads and scheduled reports.
6. **Security**: add authentication, role-based views and secret-management guidance.
7. **Deployment**: publish a reproducible hosted demo using non-sensitive synthetic data.
8. **Observability**: expose load duration, model drift and data-freshness alerts.

## Decision principle

Keep synthetic, UCI and Kaggle sources visibly separated. Extend the model only when the source actually provides the business grain; never invent customers, baskets, inventory or supplier events to make an incompatible dataset fit.

See [Public datasets](public-data.md), [Analytics](analytics.md) and [Operations](operations.md).

