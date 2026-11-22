# Verification report

Executed on 22 November 2026 against Microsoft SQL Server 2022 CU27.

## Database and ETL

| Evidence | Result |
| --- | ---: |
| Historical source records | 242,809 |
| Rejected historical records | 0 |
| Historical sales facts inserted | 160,057 |
| Historical inventory facts inserted | 9,000 |
| Historical shipment facts inserted | 4,000 |
| Historical net sales reconciled | 15,098,779.5700 |
| Run 2 fact inserts | 0 |
| Run 2 source-dimension updates | 0 |

Warehouse rows after the repeatable run:

| Object | Rows |
| --- | ---: |
| DimDate | 5,479 |
| DimProduct | 150 |
| DimStore | 10 |
| DimCustomer | 500 |
| DimChannel | 5 |
| DimPromotion | 49 |
| DimSupplier | 20 |
| FactSales | 182,176 |
| FactInventorySnapshot | 18,000 |
| FactShipment | 4,800 |

Sales cover exactly 15 calendar years, 2010-01-01 through 2024-12-31, with 73,213 transactions and 16,976,377.1400 net sales. The audit schema contains 1,607 authenticated injected-anomaly labels.

Automated verification found zero duplicate fact grains, orphaned sales facts, sales formula errors, overlapping product versions, multiple current product versions, temporal product join errors, date gaps, negative inventory records, disabled or untrusted constraints, source count differences or source sales amount differences.

The six OLAP operations, data-quality SQL and advanced reporting queries executed against SQL Server. Eleven warehouse/mart views and ten ETL/audit procedures are present.

## Automated tests

The complete test command finished with 24 passed. Coverage includes historical generation, ground-truth integrity, rolling backtests, precision/recall, dynamic dashboard forecasting and the short-range fallback that prevents the configuration error shown during UI testing.

Coverage includes deterministic generation across Python hash seeds, schema/type/range/reference validation, basket quarantine, duplicate handling, source-hash validation, non-destructive setup, public adapters, loaded warehouse counts, repeatability evidence and an SCD Type 2 change rolled back after its assertions.

## Analytics

Forecasting used 770 development weeks, five rolling-origin backtest folds and a separate unseen 12-week test. Exponential smoothing was selected using mean backtest WAPE.

| Test metric | Result |
| --- | ---: |
| Backtest mean WAPE | 12.96% |
| Backtest WAPE standard deviation | 3.63% |
| Test MAE | 2,633.60 |
| Test RMSE | 3,333.63 |
| Test WAPE | 15.26% |
| Test MASE | 0.62 |

Market-basket analysis evaluated 73,213 baskets and produced five rules at 0.2% minimum support. These associations were deliberately embedded in the generator.

RFM clustering covered 500 generated customers in four clusters with silhouette score 0.273. Isolation Forest trained on 144,471 earlier unlabeled lines, evaluated 36,241 later lines and flagged 713 for review. Against 143 injected positives in the evaluation window it achieved 12.48% precision, 62.24% recall and 0.208 F1. These figures apply only to injected high-quantity anomalies.

The problem report contains 6,239 review records covering excessive discounts, stockouts, understock, supplier delays, partial fills, sales spikes and a year-over-year decline.

The latest inventory snapshot contains 150 store-product positions: 12 stockout rows and 49 below-reorder rows. Nine generated promotions and 20 generated suppliers were evaluated.

## Dashboard

The Streamlit test harness executed the full app with zero exceptions:

- Seven functional tabs.
- 20 KPI cards.
- Nine data tables.
- Live SQL filters and KPIs.
- Forecast, basket, segmentation, inventory, supplier, anomaly and ETL panels.

## Known limitations

- All currently loaded warehouse records are synthetic demonstration data.
- No actual public dataset was supplied or loaded; adapters are implemented and fixture-tested only.
- Inventory covers 30 SKUs across five stores for 60 days.
- The system has no returns fact, stock-movement fact, purchase-order lifecycle, scheduler, orchestration service or role-based dashboard access.
- Forecast evidence uses generated data and does not establish production accuracy.
- Anomaly labels cover only injected high-quantity cases; unlabeled unusual records count as negatives in precision.
- Promotion comparisons are descriptive.
- Customer segmentation uses generated identifiers.
- The dashboard was verified with Streamlit's script harness and server startup; browser-specific visual and accessibility testing remains.

Machine-readable evidence is in reports/generated/warehouse_verification.json, reports/generated/etl_run_*.json and reports/generated/analytics/analytics_report.json.
