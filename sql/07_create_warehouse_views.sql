-- ============================================================================
-- Script: 07_create_warehouse_views.sql
-- Description: Creates dimensional reporting views in [dw] and analytical views
--              in [mart] optimized for BI tools and Power BI integration.
--              (Strictly avoids SELECT * in production reporting views)
-- ============================================================================

USE [RetailIntelligenceDW];
GO

-- ----------------------------------------------------------------------------
-- 1. dw.vw_SalesDetail
-- Flattened sales line-item view with all conformed dimension attributes.
-- ----------------------------------------------------------------------------
CREATE OR ALTER VIEW dw.vw_SalesDetail
AS
SELECT
    fs.SalesFactKey,
    fs.TransactionID,
    fs.TransactionLineID,
    d.DateKey,
    d.FullDate,
    d.DayName,
    d.WeekNumber,
    d.MonthNumber,
    d.MonthName,
    d.QuarterNumber,
    d.YearNumber,
    d.WeekendFlag,
    d.HolidayFlag,
    d.HolidayName,
    d.Season,
    p.ProductKey,
    p.SourceProductID,
    p.ProductName,
    p.Category,
    p.Subcategory,
    p.Brand,
    s.StoreKey,
    s.SourceStoreID,
    s.StoreName,
    s.StoreType,
    s.City AS StoreCity,
    s.StateOrRegion AS StoreState,
    s.SquareFootage,
    ch.ChannelName,
    pm.PromotionName,
    pm.PromotionType,
    c.SourceCustomerID,
    c.CustomerName,
    c.CustomerSegment,
    fs.QuantitySold,
    fs.UnitPrice,
    fs.GrossSalesAmount,
    fs.DiscountAmount,
    fs.NetSalesAmount,
    fs.CostAmount,
    fs.ProfitAmount,
    CAST(CASE WHEN fs.NetSalesAmount > 0
              THEN (fs.ProfitAmount / fs.NetSalesAmount) * 100.0
              ELSE 0.0 END AS DECIMAL(6,2)) AS ProfitMarginPercent,
    fs.ETLRunID
FROM dw.FactSales fs
INNER JOIN dw.DimDate d ON fs.DateKey = d.DateKey
INNER JOIN dw.DimProduct p ON fs.ProductKey = p.ProductKey
INNER JOIN dw.DimStore s ON fs.StoreKey = s.StoreKey
INNER JOIN dw.DimChannel ch ON fs.ChannelKey = ch.ChannelKey
INNER JOIN dw.DimPromotion pm ON fs.PromotionKey = pm.PromotionKey
LEFT JOIN dw.DimCustomer c ON fs.CustomerKey = c.CustomerKey;
GO

-- ----------------------------------------------------------------------------
-- 2. dw.vw_InventoryPosition
-- Real-time stock position, valuation, and replenishment risk indicators.
-- ----------------------------------------------------------------------------
CREATE OR ALTER VIEW dw.vw_InventoryPosition
AS
SELECT
    fis.InventorySnapshotKey,
    d.FullDate AS SnapshotDate,
    p.SourceProductID,
    p.ProductName,
    p.Category,
    s.SourceStoreID,
    s.StoreName,
    s.StoreType,
    s.StateOrRegion AS StoreState,
    fis.QuantityOnHand,
    fis.QuantityOnOrder,
    fis.ReorderPoint,
    fis.SafetyStock,
    fis.UnitCost,
    fis.InventoryValue,
    fis.StockoutFlag,
    fis.UnderStockFlag,
    fis.OverStockFlag,
    CASE
        WHEN fis.StockoutFlag = 1 THEN 'OUT_OF_STOCK'
        WHEN fis.UnderStockFlag = 1 THEN 'REORDER_NOW'
        WHEN fis.OverStockFlag = 1 THEN 'EXCESS_STOCK'
        ELSE 'HEALTHY'
    END AS InventoryHealthStatus
FROM dw.FactInventorySnapshot fis
INNER JOIN dw.DimDate d ON fis.DateKey = d.DateKey
INNER JOIN dw.DimProduct p ON fis.ProductKey = p.ProductKey
INNER JOIN dw.DimStore s ON fis.StoreKey = s.StoreKey;
GO

-- ----------------------------------------------------------------------------
-- 3. mart.vw_ExecutiveSalesSummary
-- Executive KPI roll-up by Year, Quarter, Month.
-- ----------------------------------------------------------------------------
CREATE OR ALTER VIEW mart.vw_ExecutiveSalesSummary
AS
SELECT
    d.YearNumber,
    d.QuarterNumber,
    d.MonthNumber,
    d.MonthName,
    COUNT(DISTINCT fs.TransactionID) AS TotalTransactions,
    SUM(fs.QuantitySold) AS TotalUnitsSold,
    SUM(fs.GrossSalesAmount) AS TotalGrossSales,
    SUM(fs.DiscountAmount) AS TotalDiscountAmount,
    SUM(fs.NetSalesAmount) AS TotalNetSales,
    SUM(fs.CostAmount) AS TotalCostAmount,
    SUM(fs.ProfitAmount) AS TotalProfitAmount,
    CAST(CASE WHEN SUM(fs.NetSalesAmount) > 0
              THEN (SUM(fs.ProfitAmount) / SUM(fs.NetSalesAmount)) * 100.0
              ELSE 0.0 END AS DECIMAL(6,2)) AS OverallProfitMarginPercent,
    CAST(CASE WHEN COUNT(DISTINCT fs.TransactionID) > 0
              THEN SUM(fs.NetSalesAmount) / COUNT(DISTINCT fs.TransactionID)
              ELSE 0.0 END AS DECIMAL(10,2)) AS AverageTransactionValue
FROM dw.FactSales fs
INNER JOIN dw.DimDate d ON fs.DateKey = d.DateKey
GROUP BY d.YearNumber, d.QuarterNumber, d.MonthNumber, d.MonthName;
GO

-- ----------------------------------------------------------------------------
-- 4. mart.vw_ProductPerformance
-- Performance metrics by category, brand, and product.
-- ----------------------------------------------------------------------------
CREATE OR ALTER VIEW mart.vw_ProductPerformance
AS
SELECT
    p.ProductKey,
    p.SourceProductID,
    p.ProductName,
    p.Category,
    p.Subcategory,
    p.Brand,
    COUNT(DISTINCT fs.TransactionID) AS OrderFrequency,
    SUM(fs.QuantitySold) AS TotalUnitsSold,
    SUM(fs.NetSalesAmount) AS TotalNetSales,
    SUM(fs.ProfitAmount) AS TotalProfitAmount,
    CAST(CASE WHEN SUM(fs.NetSalesAmount) > 0
              THEN (SUM(fs.ProfitAmount) / SUM(fs.NetSalesAmount)) * 100.0
              ELSE 0.0 END AS DECIMAL(6,2)) AS ProductProfitMarginPercent,
    RANK() OVER (ORDER BY SUM(fs.NetSalesAmount) DESC) AS SalesRank,
    RANK() OVER (PARTITION BY p.Category ORDER BY SUM(fs.NetSalesAmount) DESC) AS CategoryRank
FROM dw.FactSales fs
INNER JOIN dw.DimProduct p ON fs.ProductKey = p.ProductKey
GROUP BY p.ProductKey, p.SourceProductID, p.ProductName, p.Category, p.Subcategory, p.Brand;
GO

-- ----------------------------------------------------------------------------
-- 5. mart.vw_StorePerformance
-- Store benchmarking including sales per square foot and regional aggregation.
-- ----------------------------------------------------------------------------
CREATE OR ALTER VIEW mart.vw_StorePerformance
AS
SELECT
    s.StoreKey,
    s.SourceStoreID,
    s.StoreName,
    s.StoreType,
    s.City,
    s.StateOrRegion,
    s.SquareFootage,
    COUNT(DISTINCT fs.TransactionID) AS TotalTransactions,
    SUM(fs.QuantitySold) AS TotalUnitsSold,
    SUM(fs.NetSalesAmount) AS TotalNetSales,
    SUM(fs.ProfitAmount) AS TotalProfitAmount,
    CAST(CASE WHEN s.SquareFootage > 0
              THEN SUM(fs.NetSalesAmount) / s.SquareFootage
              ELSE 0.0 END AS DECIMAL(10,2)) AS SalesPerSquareFoot,
    RANK() OVER (ORDER BY SUM(fs.NetSalesAmount) DESC) AS StoreSalesRank
FROM dw.FactSales fs
INNER JOIN dw.DimStore s ON fs.StoreKey = s.StoreKey
GROUP BY s.StoreKey, s.SourceStoreID, s.StoreName, s.StoreType, s.City, s.StateOrRegion, s.SquareFootage;
GO

-- ----------------------------------------------------------------------------
-- 6. mart.vw_SupplierDeliveryScorecard
-- Supplier fulfillment performance, lead times, and fulfillment accuracy.
-- ----------------------------------------------------------------------------
CREATE OR ALTER VIEW mart.vw_SupplierDeliveryScorecard
AS
SELECT
    sup.SupplierKey,
    sup.SourceSupplierID,
    sup.SupplierName,
    sup.SupplierCategory,
    sup.Region,
    COUNT(fsh.ShipmentFactKey) AS TotalShipments,
    AVG(fsh.LeadTimeDays * 1.0) AS AverageLeadTimeDays,
    AVG(fsh.DaysDelayed * 1.0) AS AverageDaysDelayed,
    CAST(SUM(CASE WHEN fsh.OnTimeDeliveryFlag = 1 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(fsh.ShipmentFactKey), 0) AS DECIMAL(5,2)) AS OnTimeDeliveryRatePercent,
    CAST(SUM(CASE WHEN fsh.FullOrderFillFlag = 1 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(fsh.ShipmentFactKey), 0) AS DECIMAL(5,2)) AS FullOrderFillRatePercent,
    SUM(fsh.QuantityOrdered) AS TotalQuantityOrdered,
    SUM(fsh.QuantityReceived) AS TotalQuantityReceived
FROM dw.FactShipment fsh
INNER JOIN dw.DimSupplier sup ON fsh.SupplierKey = sup.SupplierKey
GROUP BY sup.SupplierKey, sup.SourceSupplierID, sup.SupplierName, sup.SupplierCategory, sup.Region;
GO

-- ----------------------------------------------------------------------------
-- 7. mart.vw_ETLRunSummary
-- Telemetry and audit health view for operational monitoring.
-- ----------------------------------------------------------------------------
CREATE OR ALTER VIEW mart.vw_ETLRunSummary
AS
SELECT
    ETLRunID,
    PipelineName,
    ExecutionMode,
    StartTime,
    EndTime,
    DATEDIFF(SECOND, StartTime, ISNULL(EndTime, SYSUTCDATETIME())) AS DurationSeconds,
    Status,
    SourceRowCount,
    InsertedRowCount,
    UpdatedRowCount,
    RejectedRowCount,
    ErrorMessage
FROM audit.ETLRunHistory;
GO

PRINT 'Warehouse and data mart views created successfully.';
GO
