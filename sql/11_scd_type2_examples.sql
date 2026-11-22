-- ============================================================================
-- Script: 11_scd_type2_examples.sql
-- Description: Demonstrates Slowly Changing Dimensions (SCD Type 1 & Type 2)
--              in Microsoft SQL Server, illustrating historical preservation.
-- ============================================================================

USE [RetailIntelligenceDW];
GO

BEGIN TRANSACTION; -- Example is rolled back; never included in setup.
PRINT '=== DEMONSTRATING SLOWLY CHANGING DIMENSIONS (SCD TYPE 2) ===';

-- ----------------------------------------------------------------------------
-- Step 1: Inspect an existing product in dw.DimProduct
-- ----------------------------------------------------------------------------
DECLARE @SampleSKU NVARCHAR(50) = 'PROD-001';

SELECT
    ProductKey,
    SourceProductID,
    ProductName,
    Category,
    Subcategory,
    BasePrice,
    UnitCost,
    EffectiveFrom,
    EffectiveTo,
    IsCurrent,
    VersionNumber
FROM dw.DimProduct
WHERE SourceProductID = @SampleSKU;

-- ----------------------------------------------------------------------------
-- Step 2: Simulate an operational price change in raw.SourceProduct
-- e.g., BasePrice increases from $24.99 to $29.99
-- ----------------------------------------------------------------------------
PRINT 'Simulating price revision in operational source for PROD-001...';
UPDATE raw.SourceProduct
SET BasePrice = BasePrice + 5.0000,
    ModifiedDate = SYSUTCDATETIME()
WHERE SourceProductID = @SampleSKU;

-- ----------------------------------------------------------------------------
-- Step 3: Execute the SCD Type 2 Stored Procedure
-- This will:
--   a) Expire the existing record (Set EffectiveTo = NOW, IsCurrent = 0)
--   b) Insert a new record (VersionNumber = 2, IsCurrent = 1, EffectiveFrom = NOW)
-- ----------------------------------------------------------------------------
EXEC dw.usp_LoadDimProduct_SCD2 @ETLRunID = 999;

-- ----------------------------------------------------------------------------
-- Step 4: Verify the SCD Type 2 History in dw.DimProduct
-- We should now observe two records: Version 1 (inactive) and Version 2 (active)
-- ----------------------------------------------------------------------------
PRINT 'Inspecting versioned records in dw.DimProduct:';
SELECT
    ProductKey,
    SourceProductID,
    ProductName,
    BasePrice,
    EffectiveFrom,
    EffectiveTo,
    IsCurrent,
    VersionNumber
FROM dw.DimProduct
WHERE SourceProductID = @SampleSKU
ORDER BY VersionNumber;

-- ----------------------------------------------------------------------------
-- Step 5: Verify Historical Reporting Integrity in FactSales
-- Any historical sales recorded before the change maintain their original
-- ProductKey (Version 1). Future sales record the new ProductKey (Version 2).
-- This guarantees exact historical margin and valuation preservation!
-- ----------------------------------------------------------------------------
SELECT
    p.VersionNumber,
    p.BasePrice AS CatalogPriceDuringPeriod,
    COUNT(fs.SalesFactKey) AS SalesTransactionsCount,
    SUM(fs.QuantitySold) AS UnitsSold,
    SUM(fs.NetSalesAmount) AS TotalNetRevenue
FROM dw.FactSales fs
INNER JOIN dw.DimProduct p ON fs.ProductKey = p.ProductKey
WHERE p.SourceProductID = @SampleSKU
GROUP BY p.VersionNumber, p.BasePrice;
ROLLBACK TRANSACTION;
GO
