-- ============================================================================
-- Script: 10_data_quality_checks.sql
-- Description: Automated data quality verification queries and reconciliation
--              checks between raw ingestion and the dimensional warehouse.
-- ============================================================================

USE [RetailIntelligenceDW];
GO

PRINT '====================================================================';
PRINT 'Starting Data Quality Audit Verification';
PRINT '====================================================================';

-- ----------------------------------------------------------------------------
-- Check 1: Referential Integrity Check on FactSales
-- Every record in FactSales must join to a valid Dimension key.
-- ----------------------------------------------------------------------------
SELECT
    'FactSales Referential Integrity' AS CheckName,
    COUNT(*) AS OrphanedFactRows
FROM dw.FactSales fs
LEFT JOIN dw.DimDate d ON fs.DateKey = d.DateKey
LEFT JOIN dw.DimProduct p ON fs.ProductKey = p.ProductKey
LEFT JOIN dw.DimStore s ON fs.StoreKey = s.StoreKey
LEFT JOIN dw.DimChannel ch ON fs.ChannelKey = ch.ChannelKey
WHERE d.DateKey IS NULL
   OR p.ProductKey IS NULL
   OR s.StoreKey IS NULL
   OR ch.ChannelKey IS NULL;

-- ----------------------------------------------------------------------------
-- Check 2: Duplicate Check on FactSales Grain
-- TransactionID + TransactionLineID must be unique.
-- ----------------------------------------------------------------------------
SELECT
    'FactSales Duplicate Line Grain' AS CheckName,
    COUNT(*) AS DuplicateOccurrences
FROM (
    SELECT TransactionID, TransactionLineID, COUNT(*) AS Cnt
    FROM dw.FactSales
    GROUP BY TransactionID, TransactionLineID
    HAVING COUNT(*) > 1
) dup;

-- ----------------------------------------------------------------------------
-- Check 3: Calculation Consistency in FactSales
-- Verify GrossSalesAmount, NetSalesAmount, and ProfitAmount match business formulas.
-- ----------------------------------------------------------------------------
SELECT
    'FactSales Calculation Inconsistency' AS CheckName,
    COUNT(*) AS CalculationMismatchRows
FROM dw.FactSales
WHERE ABS(GrossSalesAmount - (QuantitySold * UnitPrice)) > 0.05
   OR ABS(NetSalesAmount - (GrossSalesAmount - DiscountAmount)) > 0.05
   OR ABS(ProfitAmount - (NetSalesAmount - CostAmount)) > 0.05;

-- ----------------------------------------------------------------------------
-- Check 4: Source-to-Warehouse Reconciliation
-- Reconcile raw staging line-items against loaded dw.FactSales.
-- ----------------------------------------------------------------------------
SELECT
    'Source vs Warehouse Reconciliation' AS AuditCategory,
    (SELECT COUNT(*) FROM raw.SourceSalesTransactionLine) AS SourceLineCount,
    (SELECT COUNT(*) FROM dw.FactSales) AS WarehouseLineCount,
    (SELECT SUM(LineTotalAmount) FROM raw.SourceSalesTransactionLine) AS SourceTotalNetSales,
    (SELECT SUM(NetSalesAmount) FROM dw.FactSales) AS WarehouseTotalNetSales,
    (SELECT SUM(LineTotalAmount) FROM raw.SourceSalesTransactionLine) - (SELECT SUM(NetSalesAmount) FROM dw.FactSales) AS ReconciliationDiscrepancy;

-- ----------------------------------------------------------------------------
-- Check 5: Date Dimension Continuous Coverage Check
-- Verify there are no gaps in the calendar dimension.
-- ----------------------------------------------------------------------------
WITH DateGaps AS (
    SELECT
        FullDate,
        LEAD(FullDate) OVER (ORDER BY FullDate) AS NextDate,
        DATEDIFF(DAY, FullDate, LEAD(FullDate) OVER (ORDER BY FullDate)) AS DayDiff
    FROM dw.DimDate
)
SELECT
    'DimDate Continuity Check' AS CheckName,
    COUNT(*) AS DateGapsFound
FROM DateGaps
WHERE DayDiff > 1;

-- ----------------------------------------------------------------------------
-- Check 6: Inventory Fact Snapshot Integrity
-- No negative quantities on hand without explanation, valid costs.
-- ----------------------------------------------------------------------------
SELECT
    'Inventory Snapshot Quality' AS CheckName,
    COUNT(*) AS NegativeStockRows
FROM dw.FactInventorySnapshot
WHERE QuantityOnHand < 0 OR UnitCost < 0;

PRINT '====================================================================';
PRINT 'Data Quality Audit Verification Complete';
PRINT '====================================================================';
GO
