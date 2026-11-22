# Licenses, provenance and dataset compatibility

## Project notice

This is an educational retail analytics platform inspired by common enterprise retail patterns. It has no access to Walmart proprietary databases, internal systems, algorithms or private sales figures. The currently loaded records are explicitly labeled SYNTHETIC_CANONICAL.

## Dataset matrix

| Dataset | Terms | Native grain | Suitable analysis | Missing domains | Current status |
| --- | --- | --- | --- | --- | --- |
| Canonical retail demonstration data | Project-generated educational data | Transactions, transaction lines, products, stores, generated customers, inventory snapshots, suppliers, shipments, promotions and dates | End-to-end warehouse, OLAP, generated basket rules, forecasting, RFM, anomalies, inventory and suppliers | Real operational behavior and external validity | Generated, loaded, reconciled and verified |
| Walmart Recruiting - Store Sales Forecasting | Kaggle competition rules; user must confirm the exact download terms | Weekly sales per store and department | Weekly forecasting, holiday and markdown analysis | Transaction baskets, customers, line-item prices, inventory positions and supplier operations | Adapter implemented and fixture-tested; no actual file supplied or loaded |
| UCI Online Retail / Online Retail II | Verify the exact edition; Online Retail II is distributed under CC BY 4.0 by UCI | One invoice line | Basket analysis, RFM, returns/cancellations and line-level anomalies | Physical stores, inventory, supplier shipments and complete promotions | Adapter implemented and fixture-tested; no actual file supplied or loaded |

## Canonical generated data

The verified warehouse combines the default small dataset with a non-overlapping historical extension. It declares:

- 150 products, 10 stores, 500 generated customers and 20 suppliers.
- Calendar and sales dates from 2010-01-01 through 2024-12-31.
- 182,176 verified transaction lines across 73,213 complete transactions.
- 18,000 inventory snapshots and 4,800 generated shipment records.
- 1,607 deterministic injected high-quantity anomaly labels authenticated by manifest hashes.

The generated manifest records source system, synthetic status, seed, mode, dates, limitations, row counts and file hashes. Basket affinities are deliberately embedded and therefore must not be presented as independently discovered real retail behavior.

## Public adapter behavior

The Walmart adapter retains Store, Dept and Date as its unique weekly grain, including negative weekly sales. Optional feature and store files merge at their documented grains. It does not map weekly aggregates into transaction-line facts.

The UCI adapter retains one row per original source line, identifies cancellations or returns, preserves nullable customers and rejects malformed rows to a separate file. It does not invent physical stores, procurement, inventory or promotion facts.

Both adapters create a manifest containing input hashes, output hash, row counts, terms note, grain and limitations. Adapter output is source-specific processed data and is not silently loaded into the synthetic canonical warehouse.

## Reproducibility and privacy

Generated customer names and example.invalid email addresses are fictitious. Local .env files, generated data and trained models are ignored by Git. The local baseline backup may contain an original configuration and must not be published.

## Verified scope

Actual execution evidence covers canonical generation, validation, archive, staging, dimensions, facts, repeatable ETL, reconciliation, warehouse SQL, analytics and dashboard script execution. Public adapters are covered by fixture tests only because no public data files were provided.
