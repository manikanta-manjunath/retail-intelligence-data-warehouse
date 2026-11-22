---
title: Testing and Verification
category: quality
status: current
last_updated: 2026-11-22
tags: [testing, verification, quality, reconciliation]
---

# Testing and verification

## Automated suite

The complete suite currently passes **25 tests**.

Coverage includes:

- Deterministic generation across Python hash seeds.
- Calendar and movable-holiday correctness.
- Manifest and ground-truth hash validation.
- Type, range, reference and duplicate handling.
- Basket quarantine when a line is invalid.
- Historical prefixes, promotions and anomaly labels.
- Public Walmart and UCI normalization, including multi-sheet Excel import.
- Rolling-origin backtest chronology.
- Synthetic precision/recall calculation.
- Live SQL counts, repeatability and rolled-back SCD Type 2 behavior.
- Streamlit execution, all seven tabs and the short-range forecast fallback.

```bash
.venv/bin/python -m pytest -q
```

## Warehouse verification

The read-only verifier checks:

- Duplicate sales, inventory and shipment grains.
- Sales dimension orphans.
- Gross, net and profit formula consistency.
- Multiple current product versions and overlapping intervals.
- Temporal product joins.
- Calendar gaps.
- Negative inventory values.
- Disabled or untrusted constraints.
- Incorrect synthetic-source tags.
- Raw/fact count and amount reconciliation.
- Incomplete audit runs.

It also executes OLAP, data-quality and advanced reporting SQL to ensure the analytical layer remains runnable.

```bash
.venv/bin/python -m src.cli verify
```

## Verified warehouse snapshot

| Object | Rows |
| --- | ---: |
| `DimDate` | 5,479 |
| `DimProduct` | 150 |
| `DimStore` | 10 |
| `DimCustomer` | 500 |
| `DimPromotion` | 49 |
| `FactSales` | 182,176 |
| `FactInventorySnapshot` | 18,000 |
| `FactShipment` | 4,800 |

## Source references

- [Test suite](../tests/)
- [Verifier](../src/etl/verify.py)
- [Machine-readable verification](../reports/generated/warehouse_verification.json)
- [Human-readable verification report](../docs/VERIFICATION_REPORT.md)

