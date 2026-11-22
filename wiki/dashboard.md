---
title: Dashboard
category: presentation
status: current
last_updated: 2026-11-22
tags: [streamlit, dashboard, filters, visualization]
---

# Dashboard

The Streamlit application presents verified warehouse data through an ArgoLogics-inspired control-center design.

## Global filters

- Sales date range.
- Store locations.
- Product categories.
- Sales channels.

Executive, product and store calculations operate on the filtered sales frame. Forecasts are rebuilt and cached using the selected dates and entity filters rather than displaying a static global artifact.

## Tabs

1. **Executive**: net sales, profit, margin, transaction count, average transaction, monthly trend, category and channel views.
2. **Products & stores**: product-level table and store performance chart.
3. **Forecast**: selected model, rolling-backtest stability, unseen test metrics and future trajectory.
4. **Basket & customers**: association rules and RFM cluster profiles.
5. **Inventory & suppliers**: stock health, ABC/XYZ output and supplier scorecards.
6. **Problems & precision**: date-filtered problem records and synthetic anomaly precision/recall/F1.
7. **Anomalies & ETL**: review flags and ETL run history.

## Short-range behavior

Forecasting needs 128 complete weeks under the current configuration. Shorter selections display an information notice instead of raising a page exception. Older in-memory configuration objects are supported through default values.

## Fault tolerance

Database and artifact reads return well-formed empty frames when unavailable so the dashboard can still render its structure. This is a presentation fallback, not evidence that data processing succeeded.

## Run

```bash
./run_dashboard.sh
```

Open [http://localhost:8501](http://localhost:8501).

## Source references

- [Dashboard implementation](../dashboard/app.py)
- [Dashboard tests](../tests/test_dashboard.py)
