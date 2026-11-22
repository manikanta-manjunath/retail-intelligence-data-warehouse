---
title: Source Map
category: sources
status: current
last_updated: 2026-11-22
tags: [sources, provenance, evidence]
---

# Source map

## Repository evidence

| Evidence | Primary files |
| --- | --- |
| Runtime configuration | [settings.yaml](../config/settings.yaml), [model_config.yaml](../config/model_config.yaml), [.env.example](../.env.example) |
| Database objects | [SQL scripts](../sql/) |
| Generator and public adapters | [generator.py](../src/ingestion/generator.py), [adapters.py](../src/ingestion/adapters.py) |
| Validation and loading | [validation.py](../src/etl/validation.py), [pipeline.py](../src/etl/pipeline.py), [verify.py](../src/etl/verify.py) |
| Analytics | [forecasting.py](../src/analytics/forecasting.py), [mining.py](../src/analytics/mining.py), [problems.py](../src/analytics/problems.py), [run.py](../src/analytics/run.py) |
| Dashboard | [dashboard/app.py](../dashboard/app.py) |
| Tests | [tests](../tests/) |
| Executed evidence | [generated reports](../reports/generated/) |

## External evidence

- [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail): 541,909 invoice lines, CC BY 4.0, DOI `10.24432/C5BW33`.
- [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii): 1,067,371 invoice lines across two years, CC BY 4.0, DOI `10.24432/C5CG6D`.
- [Walmart Recruiting — Store Sales Forecasting](https://www.kaggle.com/competitions/walmart-recruiting-store-sales-forecasting/data): weekly store-department data governed by Kaggle competition rules.

See [Public datasets](public-data.md) for compatibility and commands.
