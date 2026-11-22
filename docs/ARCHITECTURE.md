# Architecture and schema

## Processing flow

Canonical CSVs and manifest
→ Python type and business validation
→ immutable raw.IngestedRecord archive
→ run-scoped staging
→ current raw source state
→ conformed dimensions and atomic facts
→ reporting marts
→ model artifacts and Streamlit dashboard.

Rejected rows go to audit.RejectedRecord. The audit schema connects every archive, staging row, rejection, fact and quality result to an ETL run.

Each input manifest declares source system, synthetic status, row counts, limitations and SHA-256 hashes. The loader verifies hashes before parsing. Every original row is archived as JSON with its own hash before accepted rows enter the warehouse transaction.

## Schemas

| Schema | Purpose |
| --- | --- |
| raw | Immutable row archive and latest accepted source-state tables |
| stg | Accepted records scoped by ETLRunID |
| dw | Conformed dimensions, historical versions and facts |
| mart | Reporting and model-ready views |
| audit | Runs, manifests, rejected records, synthetic ground truth and data-quality logs |

## Dimensions

| Dimension | Business key | History |
| --- | --- | --- |
| DimDate | DateKey / FullDate | Static calendar |
| DimProduct | SourceProductID | SCD Type 2 for price, cost, hierarchy, brand, UOM and supplier |
| DimStore | SourceStoreID | Type 1 overwrite |
| DimCustomer | SourceCustomerID | Type 1 overwrite |
| DimChannel | ChannelName | Insert new values |
| DimPromotion | PromotionID | Type 1 overwrite |
| DimSupplier | SourceSupplierID | Type 1 overwrite |

The first product version starts at 1900-01-01, representing an unknown earlier effective date. Later versions start at the observed source modification timestamp. Sales resolve the product version at the full transaction timestamp; inventory and shipments resolve it at their business date.

## Facts and grain

| Fact | Grain | Uniqueness guard | Main measures |
| --- | --- | --- | --- |
| FactSales | One transaction product line | TransactionID plus TransactionLineID | quantity, gross sales, discount, net sales, cost, profit |
| FactInventorySnapshot | One date, product and store | DateKey plus ProductKey plus StoreKey | on hand, on order, reorder point, value, health flags |
| FactShipment | One shipment | ShipmentID | ordered/received quantity, lead time, delay, fill flags |

Foreign keys enforce conformed dimensions. Check constraints enforce non-negative measures and sales formulas. Raw business keys and current dimension business keys have unique indexes.

## Transaction and recovery behavior

An application lock serializes warehouse writers. Staging, current-source synchronization, dimension loads, facts, data-quality rows and successful audit completion commit as one warehouse transaction. An exception rolls it back and records the run as failed. Immutable source archives are retained for diagnosis.

Reruns use raw and fact business keys. An identical batch creates a new audit/archive run but inserts no duplicate facts. Changes to mutable dimension sources are synchronized; a conflicting immutable sales, inventory or shipment key aborts the warehouse transaction.

## Analytics

- Weekly forecasting uses complete calendar weeks, up to five expanding-window rolling-origin folds for model selection and a separate unseen 12-week test. Recursive predictions do not consume fold/test targets.
- Market-basket analysis uses distinct product membership within generated transaction IDs.
- RFM K-means excludes anonymous transactions and reports silhouette score instead of classification accuracy.
- Isolation Forest uses a chronological 80/20 split, excludes injected labels from training, and reports precision, recall, F1 and confusion counts only against authenticated synthetic injections.
- Problem detection reports sales spikes/drops, year-over-year decline, low margins, excessive discounts, missing dates, stockouts, understock, supplier delay/partial fill and ETL quality failures.
- Dashboard forecasts are recalculated and cached by selected date range, stores, categories and channels.
- Inventory ABC/XYZ, promotion comparisons and supplier scorecards are descriptive.

## Public sources

Public adapters write source-specific processed files and manifests. Walmart weekly records remain weekly store-department observations. UCI records remain invoice lines with cancellations identified. Neither adapter fabricates missing canonical business domains.
