---
title: Analytics and Data Mining
category: analytics
status: current
last_updated: 2026-11-22
tags: [forecasting, anomaly-detection, clustering, market-basket]
---

# Analytics and data mining

Analytics run only after warehouse verification passes. Every run records a warehouse signature so outputs can be tied to the source snapshot.

## Weekly sales forecasting

Daily sales are completed against the calendar, zero-filled and aggregated into full Monday-based weeks. Five candidate models are evaluated: naive, four-week moving average, exponential smoothing, random forest and gradient boosting.

Model selection uses up to five non-overlapping expanding-window rolling-origin folds. The final 12 weeks remain unseen until test evaluation. The selected model is refit on all history before producing a 12-week future forecast.

Verified selected model: **exponential smoothing**.

| Measure | Result |
| --- | ---: |
| Mean backtest WAPE | 12.96% |
| Backtest WAPE standard deviation | 3.63% |
| Unseen-test WAPE | 15.26% |
| Unseen-test MASE | 0.62 |

These are synthetic-data results, not a production service-level guarantee.

## Market-basket analysis

FP-Growth uses distinct products within each transaction. The verified run evaluated 73,213 baskets and produced five association rules at 0.2% minimum support. Associations are partly embedded by the generator and must be presented as demonstration evidence.

## Customer segmentation

K-means clusters generated customers using log-transformed and standardized recency, frequency and monetary features. Four clusters cover 500 customer identifiers with a silhouette score of approximately 0.273. This is descriptive segmentation, not supervised accuracy.

## Anomaly evaluation

Isolation Forest uses quantity, unit price, net sales and discount. The split is chronological: 80% training and 20% evaluation. Known injected anomalies are excluded from training.

| Measure | Result |
| --- | ---: |
| Evaluation lines | 36,241 |
| Injected positives | 143 |
| Flagged lines | 713 |
| Precision | 12.48% |
| Recall | 62.24% |
| F1 | 0.208 |

These metrics apply only to deterministic injected high-quantity anomalies. Unlabeled unusual behavior counts as negative, and the figures do not measure fraud detection.

## Business-problem detection

The problem report identifies sales spikes/drops, year-over-year decline, low/negative margins, excessive discounts, missing sales dates, stockouts, understock, supplier delays, partial fills and failed quality checks. The verified output contains 6,239 review records.

## Other analyses

- Inventory ABC/XYZ classification and latest stock health.
- Descriptive before/during promotion comparison.
- Supplier delivery, delay and fill-rate scorecards.

## Source references

- [Forecasting](../src/analytics/forecasting.py)
- [Mining](../src/analytics/mining.py)
- [Problem detection](../src/analytics/problems.py)
- [Analytics orchestration](../src/analytics/run.py)
- [Analytics report](../reports/generated/analytics/analytics_report.json)

