-- ============================================================================
-- Script: 12_reporting_queries.sql
-- Description: Advanced T-SQL analytical queries showcasing Window Functions,
--              CTEs, Rankings, Cumulative Totals, Moving Averages, and YoY/WoW.
-- ============================================================================

USE [RetailIntelligenceDW];
GO

-- ----------------------------------------------------------------------------
-- 1. Total Revenue, Units Sold, and Gross Profit
-- ----------------------------------------------------------------------------
SELECT
    COUNT(DISTINCT TransactionID) AS TotalTransactions,
    SUM(QuantitySold) AS TotalUnitsSold,
    SUM(GrossSalesAmount) AS TotalGrossSales,
    SUM(DiscountAmount) AS TotalDiscountsGiven,
    SUM(NetSalesAmount) AS TotalNetSales,
    SUM(ProfitAmount) AS TotalGrossProfit,
    CAST(SUM(ProfitAmount) * 100.0 / NULLIF(SUM(NetSalesAmount), 0) AS DECIMAL(5,2)) AS OverallGrossMarginPct
FROM dw.FactSales;

-- ----------------------------------------------------------------------------
-- 2. Top 10 Products by Net Revenue with Category Ranking
-- ----------------------------------------------------------------------------
WITH RankedProducts AS (
    SELECT
        p.SourceProductID,
        p.ProductName,
        p.Category,
        SUM(fs.QuantitySold) AS UnitsSold,
        SUM(fs.NetSalesAmount) AS TotalNetRevenue,
        SUM(fs.ProfitAmount) AS TotalProfit,
        DENSE_RANK() OVER (ORDER BY SUM(fs.NetSalesAmount) DESC) AS OverallRank,
        ROW_NUMBER() OVER (PARTITION BY p.Category ORDER BY SUM(fs.NetSalesAmount) DESC) AS CategoryRank
    FROM dw.FactSales fs
    INNER JOIN dw.DimProduct p ON fs.ProductKey = p.ProductKey
    GROUP BY p.SourceProductID, p.ProductName, p.Category
)
SELECT TOP 10
    OverallRank,
    CategoryRank,
    SourceProductID,
    ProductName,
    Category,
    UnitsSold,
    TotalNetRevenue,
    TotalProfit
FROM RankedProducts
ORDER BY OverallRank;

-- ----------------------------------------------------------------------------
-- 3. Bottom 10 Products with Minimum Volume Safeguards
-- (Protects against newly listed items with negligible exposure)
-- ----------------------------------------------------------------------------
SELECT TOP 10
    p.SourceProductID,
    p.ProductName,
    p.Category,
    SUM(fs.QuantitySold) AS UnitsSold,
    SUM(fs.NetSalesAmount) AS TotalNetRevenue
FROM dw.FactSales fs
INNER JOIN dw.DimProduct p ON fs.ProductKey = p.ProductKey
GROUP BY p.SourceProductID, p.ProductName, p.Category
HAVING SUM(fs.QuantitySold) >= 10 -- Minimum volume threshold
ORDER BY TotalNetRevenue ASC;

-- ----------------------------------------------------------------------------
-- 4. Running Totals & Cumulative Sales by Month
-- Window function: SUM() OVER (PARTITION BY ... ORDER BY ...)
-- ----------------------------------------------------------------------------
SELECT
    d.YearNumber,
    d.MonthNumber,
    d.MonthName,
    SUM(fs.NetSalesAmount) AS MonthlyRevenue,
    SUM(SUM(fs.NetSalesAmount)) OVER (
        PARTITION BY d.YearNumber
        ORDER BY d.MonthNumber
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS CumulativeYearToDateRevenue
FROM dw.FactSales fs
INNER JOIN dw.DimDate d ON fs.DateKey = d.DateKey
GROUP BY d.YearNumber, d.MonthNumber, d.MonthName
ORDER BY d.YearNumber, d.MonthNumber;

-- ----------------------------------------------------------------------------
-- 5. 7-Day Moving Average of Daily Sales
-- Window function: AVG() OVER (ORDER BY ... ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
-- ----------------------------------------------------------------------------
WITH DailySales AS (
    SELECT
        d.FullDate,
        SUM(fs.NetSalesAmount) AS DailySalesAmount
    FROM dw.FactSales fs
    INNER JOIN dw.DimDate d ON fs.DateKey = d.DateKey
    GROUP BY d.FullDate
)
SELECT
    FullDate,
    DailySalesAmount,
    AVG(DailySalesAmount) OVER (
        ORDER BY FullDate
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS MovingAvg7Days
FROM DailySales
ORDER BY FullDate;

-- ----------------------------------------------------------------------------
-- 6. Year-over-Year (YoY) Sales Comparison using LAG()
-- ----------------------------------------------------------------------------
WITH MonthlySales AS (
    SELECT
        d.YearNumber,
        d.MonthNumber,
        d.MonthName,
        SUM(fs.NetSalesAmount) AS CurrentYearSales
    FROM dw.FactSales fs
    INNER JOIN dw.DimDate d ON fs.DateKey = d.DateKey
    GROUP BY d.YearNumber, d.MonthNumber, d.MonthName
)
SELECT
    YearNumber,
    MonthNumber,
    MonthName,
    CurrentYearSales,
    LAG(CurrentYearSales, 1) OVER (
        PARTITION BY MonthNumber
        ORDER BY YearNumber
    ) AS PriorYearSales,
    CAST((CurrentYearSales - LAG(CurrentYearSales, 1) OVER (PARTITION BY MonthNumber ORDER BY YearNumber)) * 100.0 /
         NULLIF(LAG(CurrentYearSales, 1) OVER (PARTITION BY MonthNumber ORDER BY YearNumber), 0) AS DECIMAL(6,2)) AS YoYGrowthPercent
FROM MonthlySales
ORDER BY MonthNumber, YearNumber;

-- ----------------------------------------------------------------------------
-- 7. Inventory Stockout Risk & Replenishment Priority Ranking
-- ----------------------------------------------------------------------------
SELECT TOP 20
    s.StoreName,
    p.ProductName,
    p.Category,
    fis.QuantityOnHand,
    fis.ReorderPoint,
    fis.SafetyStock,
    (fis.ReorderPoint - fis.QuantityOnHand) AS ReorderDeficit,
    DENSE_RANK() OVER (ORDER BY (fis.ReorderPoint - fis.QuantityOnHand) DESC) AS ReplenishmentPriorityRank
FROM dw.FactInventorySnapshot fis
INNER JOIN dw.DimDate d ON fis.DateKey = d.DateKey
INNER JOIN dw.DimStore s ON fis.StoreKey = s.StoreKey
INNER JOIN dw.DimProduct p ON fis.ProductKey = p.ProductKey
WHERE fis.QuantityOnHand < fis.ReorderPoint
  AND d.FullDate = (SELECT MAX(FullDate) FROM dw.DimDate INNER JOIN dw.FactInventorySnapshot f ON dw.DimDate.DateKey = f.DateKey)
ORDER BY ReplenishmentPriorityRank;
GO
