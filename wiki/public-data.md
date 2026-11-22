---
title: Public Retail Datasets
category: datasets
status: current
last_updated: 2026-11-22
tags: [public-data, uci, kaggle, licensing]
---

# Public retail datasets

## Recommended: UCI Online Retail II

[UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) contains 1,067,371 real invoice lines from a UK non-store retailer between December 2009 and December 2011. It is licensed under CC BY 4.0 and has DOI `10.24432/C5CG6D`.

Use it for basket analysis, RFM, cancellation/return behavior and line-level anomaly studies. The adapter imports every workbook worksheet and preserves original row identity.

```bash
.venv/bin/python -m src.cli adapt-public \
  --dataset uci-online-retail \
  --primary data/raw/public/online_retail_II.xlsx \
  --output data/processed/uci-online-retail-ii
```

## Smaller UCI alternative

[UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail) contains 541,909 invoice lines from December 2010 through December 2011. It is also CC BY 4.0 and has DOI `10.24432/C5BW33`.

## Walmart weekly forecasting data

[Walmart Recruiting — Store Sales Forecasting](https://www.kaggle.com/competitions/walmart-recruiting-store-sales-forecasting/data) provides weekly department sales for 45 stores plus store attributes, holidays, markdowns and regional economic variables. Download requires a Kaggle account and acceptance of the competition rules.

```bash
.venv/bin/python -m src.cli adapt-public \
  --dataset walmart-weekly \
  --primary data/raw/public/walmart/train.csv \
  --features data/raw/public/walmart/features.csv \
  --stores data/raw/public/walmart/stores.csv \
  --output data/processed/walmart-weekly
```

## Compatibility boundary

| Source | Native grain | Do not infer |
| --- | --- | --- |
| UCI Online Retail | Invoice line | Physical stores, inventory, suppliers or complete promotions |
| Walmart Recruiting | Store/department/week | Transaction baskets, customers, item prices or procurement events |

Adapters normalize and hash these sources but do not mix them into canonical facts. Integration requires a deliberate source-specific warehouse design rather than fabricated fields.

## Attribution

UCI usage must credit Daqing Chen, the UCI Machine Learning Repository and the relevant DOI. Walmart data use must comply with the current Kaggle competition rules.

## Source references

- [Public adapters](../src/ingestion/adapters.py)
- [Adapter tests](../tests/test_public_adapters.py)
- [Licenses and source matrix](../LICENSES_AND_DATA_SOURCES.md)

