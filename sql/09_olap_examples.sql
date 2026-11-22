-- ============================================================================
-- Script: 09_olap_examples.sql
-- Description: Demonstrates core OLAP operations (Roll-up, Drill-down, Slice,
--              Dice, Pivot, Drill-through) using executable T-SQL queries.
-- ============================================================================

USE [RetailIntelligenceDW];
GO

-- ============================================================================
-- 1. ROLL-UP OPERATION
-- Business Question: What are the sales totals aggregated from Year down to
--                    Quarter, Month, and grand total?
-- Concept: Roll-up moves up the concept hierarchy by summarizing lower-level
--          dimensions into higher-level aggregates.
-- ============================================================================
SELECT
    d.YearNumber,
    d.QuarterNumber,
    d.MonthName,
    SUM(fs.QuantitySold) AS TotalUnitsSold,
    SUM(fs.NetSalesAmount) AS TotalNetRevenue,
    SUM(fs.ProfitAmount) AS TotalProfit
FROM dw.FactSales fs
INNER JOIN dw.DimDate d ON fs.DateKey = d.DateKey
GROUP BY ROLLUP (d.YearNumber, d.QuarterNumber, d.MonthName)
ORDER BY d.YearNumber, d.QuarterNumber, d.MonthName;
GO

-- ============================================================================
-- 2. DRILL-DOWN OPERATION
-- Business Question: Break down total sales from geographical Region -> Store ->
--                    Product Category to inspect low-performing departments.
-- Concept: Drill-down moves down the concept hierarchy, expanding summary
--          data into finer granularities.
-- ============================================================================
SELECT
    s.StateOrRegion,
    s.StoreName,
    p.Category,
    COUNT(DISTINCT fs.TransactionID) AS TotalTransactions,
    SUM(fs.QuantitySold) AS UnitsSold,
    SUM(fs.NetSalesAmount) AS NetSalesAmount,
    CAST(SUM(fs.ProfitAmount) * 100.0 / NULLIF(SUM(fs.NetSalesAmount), 0) AS DECIMAL(5,2)) AS ProfitMarginPct
FROM dw.FactSales fs
INNER JOIN dw.DimStore s ON fs.StoreKey = s.StoreKey
INNER JOIN dw.DimProduct p ON fs.ProductKey = p.ProductKey
GROUP BY s.StateOrRegion, s.StoreName, p.Category
ORDER BY s.StateOrRegion, s.StoreName, NetSalesAmount DESC;
GO

-- ============================================================================
-- 3. SLICE OPERATION
-- Business Question: What were the category sales specifically for the 'Online'
--                    channel during Year 2024?
-- Concept: Slicing fixes one dimension to a single coordinate (Channel = 'Online'
--          and Year = 2024), extracting a sub-cube.
-- ============================================================================
SELECT
    p.Category,
    p.Subcategory,
    SUM(fs.QuantitySold) AS OnlineUnitsSold,
    SUM(fs.NetSalesAmount) AS OnlineNetSales,
    SUM(fs.ProfitAmount) AS OnlineProfit
FROM dw.FactSales fs
INNER JOIN dw.DimChannel ch ON fs.ChannelKey = ch.ChannelKey
INNER JOIN dw.DimDate d ON fs.DateKey = d.DateKey
INNER JOIN dw.DimProduct p ON fs.ProductKey = p.ProductKey
WHERE ch.ChannelName = 'Online'
  AND d.YearNumber = 2024
GROUP BY p.Category, p.Subcategory
ORDER BY OnlineNetSales DESC;
GO

-- ============================================================================
-- 4. DICE OPERATION
-- Business Question: Compare sales for specific categories ('Electronics', 'Grocery')
--                    across specific regions ('South', 'Midwest') in Q4.
-- Concept: Dicing selects two or more dimensions within specific ranges,
--          generating a smaller multidimensional sub-cube.
-- ============================================================================
SELECT
    s.StateOrRegion,
    p.Category,
    d.MonthName,
    SUM(fs.QuantitySold) AS UnitsSold,
    SUM(fs.NetSalesAmount) AS NetRevenue
FROM dw.FactSales fs
INNER JOIN dw.DimStore s ON fs.StoreKey = s.StoreKey
INNER JOIN dw.DimProduct p ON fs.ProductKey = p.ProductKey
INNER JOIN dw.DimDate d ON fs.DateKey = d.DateKey
WHERE p.Category IN ('Electronics', 'Grocery')
  AND s.StateOrRegion IN ('South', 'Midwest')
  AND d.QuarterNumber = 4
GROUP BY s.StateOrRegion, p.Category, d.MonthName
ORDER BY s.StateOrRegion, p.Category, d.MonthName;
GO

-- ============================================================================
-- 5. PIVOT OPERATION
-- Business Question: Pivot total quarterly revenue into columns by Product Category
--                    to easily compare performance side-by-side.
-- Concept: Transposes rows into columns for cross-tabular multidimensional layout.
-- ============================================================================
SELECT
    Category,
    ISNULL([Q1], 0.00) AS Q1_Sales,
    ISNULL([Q2], 0.00) AS Q2_Sales,
    ISNULL([Q3], 0.00) AS Q3_Sales,
    ISNULL([Q4], 0.00) AS Q4_Sales,
    ISNULL([Q1], 0.00) + ISNULL([Q2], 0.00) + ISNULL([Q3], 0.00) + ISNULL([Q4], 0.00) AS Annual_Total
FROM (
    SELECT
        p.Category,
        'Q' + CAST(d.QuarterNumber AS VARCHAR(1)) AS QuarterName,
        fs.NetSalesAmount
    FROM dw.FactSales fs
    INNER JOIN dw.DimDate d ON fs.DateKey = d.DateKey
    INNER JOIN dw.DimProduct p ON fs.ProductKey = p.ProductKey
    WHERE d.YearNumber = 2024
) AS SourceData
PIVOT (
    SUM(NetSalesAmount)
    FOR QuarterName IN ([Q1], [Q2], [Q3], [Q4])
) AS PivotTable
ORDER BY Annual_Total DESC;
GO

-- ============================================================================
-- 6. DRILL-THROUGH OPERATION
-- Business Question: Given a summary metric (e.g. high sales on Black Friday /
--                    Christmas Eve in Store #1), drill through to the exact
--                    underlying transaction line items that composed it.
-- Concept: Drills from the aggregate dimensional cell down to the individual
--          atomic fact records and transactional audit keys.
-- ============================================================================
SELECT TOP 50
    fs.SalesFactKey,
    fs.TransactionID,
    fs.TransactionLineID,
    d.FullDate,
    s.StoreName,
    p.ProductName,
    p.Category,
    ch.ChannelName,
    fs.QuantitySold,
    fs.UnitPrice,
    fs.GrossSalesAmount,
    fs.DiscountAmount,
    fs.NetSalesAmount,
    fs.ProfitAmount,
    fs.CreatedTimestamp
FROM dw.FactSales fs
INNER JOIN dw.DimDate d ON fs.DateKey = d.DateKey
INNER JOIN dw.DimStore s ON fs.StoreKey = s.StoreKey
INNER JOIN dw.DimProduct p ON fs.ProductKey = p.ProductKey
INNER JOIN dw.DimChannel ch ON fs.ChannelKey = ch.ChannelKey
WHERE s.SourceStoreID = 'STORE-001'
  AND d.FullDate = '2024-11-29' -- Target date (e.g., Black Friday)
ORDER BY fs.NetSalesAmount DESC;
GO
