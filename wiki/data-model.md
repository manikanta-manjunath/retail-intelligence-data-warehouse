---
title: Warehouse Data Model
category: data-model
status: current
last_updated: 2026-11-22
tags: [dimensional-model, facts, dimensions, scd]
---

# Warehouse data model

## Dimensions

| Dimension | Business key | History strategy |
| --- | --- | --- |
| `DimDate` | `DateKey` / `FullDate` | Static calendar |
| `DimProduct` | `SourceProductID` | SCD Type 2 for commercial and hierarchy attributes |
| `DimStore` | `SourceStoreID` | Type 1 overwrite |
| `DimCustomer` | `SourceCustomerID` | Type 1 overwrite, including `JoinDate` |
| `DimChannel` | `ChannelName` | Insert new values |
| `DimPromotion` | `PromotionID` | Type 1 overwrite |
| `DimSupplier` | `SourceSupplierID` | Type 1 overwrite |

The first product version begins at `1900-01-01`, representing an unknown prior effective date. Later versions begin at the observed modification timestamp. Sales resolve the correct product version at the transaction timestamp; inventory and shipments use their business dates.

## Facts

| Fact | Grain | Unique business key | Main measures |
| --- | --- | --- | --- |
| `FactSales` | One product line in one transaction | `TransactionID`, `TransactionLineID` | quantity, gross, discount, net, cost, profit |
| `FactInventorySnapshot` | One product/store/date position | `DateKey`, `ProductKey`, `StoreKey` | on hand, on order, reorder point, value, health flags |
| `FactShipment` | One shipment | `ShipmentID` | ordered/received quantity, lead time, delay and fill flags |

## Enforcement

- Foreign keys enforce conformed dimension references.
- Unique indexes protect raw business keys, current dimension keys and fact grains.
- Check constraints enforce non-negative values and sales arithmetic.
- Verification queries detect duplicate grains, orphans, date gaps, formula errors and temporal-product mismatches.

## Reporting layer

Eleven `dw` and `mart` views provide flattened sales detail, inventory position, executive summaries, product/store performance, supplier delivery, ETL history, RFM, daily store sales, weekly category sales and inventory risk.

## Source references

- [Dimension definitions](../sql/03_create_dimensions.sql)
- [Fact definitions](../sql/04_create_fact_tables.sql)
- [Constraints and indexes](../sql/05_create_constraints_indexes.sql)
- [Reliability migration](../sql/14_etl_reliability.sql)
- [Reporting views](../sql/07_create_warehouse_views.sql)
- [Analytical marts](../sql/08_create_data_marts.sql)

