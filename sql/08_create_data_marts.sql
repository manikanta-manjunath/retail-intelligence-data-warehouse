-- ============================================================================
-- Script: 08_create_data_marts.sql
-- Description: Creates specialized analytical data marts for Sales, Products,
--              Inventory, and Customer RFM analytics.
-- ============================================================================

USE [RetailIntelligenceDW];
GO

-- ----------------------------------------------------------------------------
-- 1. mart.vw_CustomerRFMSummary
-- Customer-level RFM aggregations for data mining and clustering algorithms.
-- ----------------------------------------------------------------------------
CREATE OR ALTER VIEW mart.vw_CustomerRFMSummary
AS
WITH ReferenceDate AS (
    SELECT MAX(FullDate) AS MaxSalesDate FROM dw.DimDate d
    INNER JOIN dw.FactSales fs ON d.DateKey = fs.DateKey
),
CustomerSales AS (
    SELECT
        c.CustomerKey,
        c.SourceCustomerID,
        c.CustomerName,
        c.CustomerSegment,
        c.City,
        c.StateOrRegion,
        MAX(d.FullDate) AS LastPurchaseDate,
        COUNT(DISTINCT fs.TransactionID) AS Frequency,
        SUM(fs.NetSalesAmount) AS Monetary,
        SUM(fs.QuantitySold) AS TotalUnits,
        AVG(fs.NetSalesAmount) AS AverageLineValue
    FROM dw.FactSales fs
    INNER JOIN dw.DimCustomer c ON fs.CustomerKey = c.CustomerKey
    INNER JOIN dw.DimDate d ON fs.DateKey = d.DateKey
    GROUP BY c.CustomerKey, c.SourceCustomerID, c.CustomerName, c.CustomerSegment, c.City, c.StateOrRegion
)
SELECT
    cs.CustomerKey,
    cs.SourceCustomerID,
    cs.CustomerName,
    cs.CustomerSegment,
    cs.City,
    cs.StateOrRegion,
    DATEDIFF(DAY, cs.LastPurchaseDate, ref.MaxSalesDate) AS RecencyDays,
    cs.Frequency,
    cs.Monetary,
    CAST(cs.Monetary / NULLIF(cs.Frequency, 0) AS DECIMAL(10,2)) AS AverageOrderValue,
    cs.TotalUnits,
    cs.LastPurchaseDate
FROM CustomerSales cs
CROSS JOIN ReferenceDate ref;
GO

-- ----------------------------------------------------------------------------
-- 2. mart.vw_StoreDailySalesSummary
-- Daily store level sales time series view for demand forecasting models.
-- ----------------------------------------------------------------------------
CREATE OR ALTER VIEW mart.vw_StoreDailySalesSummary
AS
SELECT
    d.DateKey,
    d.FullDate,
    d.YearNumber,
    d.MonthNumber,
    d.WeekNumber,
    d.DayOfWeek,
    d.DayName,
    d.WeekendFlag,
    d.HolidayFlag,
    s.StoreKey,
    s.SourceStoreID,
    s.StoreName,
    s.StoreType,
    s.StateOrRegion,
    p.Category,
    COUNT(DISTINCT fs.TransactionID) AS TransactionCount,
    SUM(fs.QuantitySold) AS TotalUnitsSold,
    SUM(fs.NetSalesAmount) AS TotalNetSales,
    SUM(fs.ProfitAmount) AS TotalProfitAmount
FROM dw.FactSales fs
INNER JOIN dw.DimDate d ON fs.DateKey = d.DateKey
INNER JOIN dw.DimStore s ON fs.StoreKey = s.StoreKey
INNER JOIN dw.DimProduct p ON fs.ProductKey = p.ProductKey
GROUP BY
    d.DateKey, d.FullDate, d.YearNumber, d.MonthNumber, d.WeekNumber,
    d.DayOfWeek, d.DayName, d.WeekendFlag, d.HolidayFlag,
    s.StoreKey, s.SourceStoreID, s.StoreName, s.StoreType, s.StateOrRegion,
    p.Category;
GO

-- ----------------------------------------------------------------------------
-- 3. mart.vw_CategoryWeeklySales
-- Weekly category demand aggregates for high-level time series forecasting.
-- ----------------------------------------------------------------------------
CREATE OR ALTER VIEW mart.vw_CategoryWeeklySales
AS
SELECT
    d.YearNumber,
    d.WeekNumber,
    MIN(d.FullDate) AS WeekStartDate,
    p.Category,
    COUNT(DISTINCT fs.TransactionID) AS TotalOrders,
    SUM(fs.QuantitySold) AS TotalQuantity,
    SUM(fs.NetSalesAmount) AS TotalRevenue,
    SUM(fs.ProfitAmount) AS TotalProfit,
    MAX(CAST(d.HolidayFlag AS INT)) AS HasHolidayInWeek
FROM dw.FactSales fs
INNER JOIN dw.DimDate d ON fs.DateKey = d.DateKey
INNER JOIN dw.DimProduct p ON fs.ProductKey = p.ProductKey
GROUP BY d.YearNumber, d.WeekNumber, p.Category;
GO

-- ----------------------------------------------------------------------------
-- 4. mart.vw_InventoryRiskSummary
-- Daily inventory health summary by store and category.
-- ----------------------------------------------------------------------------
CREATE OR ALTER VIEW mart.vw_InventoryRiskSummary
AS
SELECT
    d.FullDate AS SnapshotDate,
    s.StoreName,
    p.Category,
    COUNT(fis.InventorySnapshotKey) AS TotalSKUsTracked,
    SUM(fis.QuantityOnHand) AS TotalUnitsOnHand,
    SUM(fis.InventoryValue) AS TotalInventoryValue,
    SUM(CAST(fis.StockoutFlag AS INT)) AS StockoutSKUCount,
    SUM(CAST(fis.UnderStockFlag AS INT)) AS ReorderSKUCount,
    SUM(CAST(fis.OverStockFlag AS INT)) AS ExcessSKUCount
FROM dw.FactInventorySnapshot fis
INNER JOIN dw.DimDate d ON fis.DateKey = d.DateKey
INNER JOIN dw.DimStore s ON fis.StoreKey = s.StoreKey
INNER JOIN dw.DimProduct p ON fis.ProductKey = p.ProductKey
GROUP BY d.FullDate, s.StoreName, p.Category;
GO

PRINT 'Data marts created successfully in mart schema.';
GO
