-- ============================================================================
-- Script: 04_create_fact_tables.sql
-- Description: Creates the fact tables in the [dw] schema with explicit
--              granularity, surrogate keys, measures, and audit columns.
-- ============================================================================

USE [RetailIntelligenceDW];
GO

-- ----------------------------------------------------------------------------
-- 1. FactSales
-- Grain: Exactly one row per product line item in a sales transaction.
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.FactSales', N'U') IS NULL
BEGIN
    CREATE TABLE dw.FactSales (
        SalesFactKey BIGINT IDENTITY(1,1) PRIMARY KEY,
        -- Degenerate Dimensions
        TransactionID NVARCHAR(60) NOT NULL,
        TransactionLineID INT NOT NULL,
        -- Foreign Keys to Dimensions
        DateKey INT NOT NULL,
        ProductKey INT NOT NULL,
        StoreKey INT NOT NULL,
        ChannelKey INT NOT NULL,
        PromotionKey INT NOT NULL DEFAULT 0,
        CustomerKey INT NULL, -- Nullable if anonymous guest checkout
        -- Additive Numerical Measures
        QuantitySold INT NOT NULL,
        UnitPrice DECIMAL(12, 4) NOT NULL,
        GrossSalesAmount DECIMAL(14, 4) NOT NULL, -- QuantitySold * UnitPrice
        DiscountAmount DECIMAL(12, 4) NOT NULL DEFAULT 0.0000,
        NetSalesAmount DECIMAL(14, 4) NOT NULL,   -- GrossSalesAmount - DiscountAmount
        CostAmount DECIMAL(14, 4) NOT NULL,       -- QuantitySold * Product UnitCost
        ProfitAmount DECIMAL(14, 4) NOT NULL,     -- NetSalesAmount - CostAmount
        -- Audit & Traceability
        SourceSystem NVARCHAR(50) NOT NULL DEFAULT 'UNDECLARED',
        ETLRunID INT NOT NULL DEFAULT 1,
        CreatedTimestamp DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
GO

-- ----------------------------------------------------------------------------
-- 2. FactInventorySnapshot
-- Grain: One record per product, per store, per daily snapshot date.
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.FactInventorySnapshot', N'U') IS NULL
BEGIN
    CREATE TABLE dw.FactInventorySnapshot (
        InventorySnapshotKey BIGINT IDENTITY(1,1) PRIMARY KEY,
        DateKey INT NOT NULL,
        ProductKey INT NOT NULL,
        StoreKey INT NOT NULL,
        -- Semi-additive and additive measures
        QuantityOnHand INT NOT NULL,
        QuantityOnOrder INT NOT NULL DEFAULT 0,
        ReorderPoint INT NOT NULL,
        SafetyStock INT NOT NULL,
        UnitCost DECIMAL(12, 4) NOT NULL,
        InventoryValue DECIMAL(16, 4) NOT NULL, -- QuantityOnHand * UnitCost
        -- Heuristic Analytical Flags
        StockoutFlag BIT NOT NULL DEFAULT 0,    -- 1 if QuantityOnHand <= 0
        UnderStockFlag BIT NOT NULL DEFAULT 0,  -- 1 if QuantityOnHand < ReorderPoint
        OverStockFlag BIT NOT NULL DEFAULT 0,   -- 1 if QuantityOnHand > (ReorderPoint * 3)
        -- Audit
        ETLRunID INT NOT NULL DEFAULT 1,
        CreatedTimestamp DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
GO

-- ----------------------------------------------------------------------------
-- 3. FactShipment
-- Grain: One record per supplier purchase-order shipment delivery event.
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.FactShipment', N'U') IS NULL
BEGIN
    CREATE TABLE dw.FactShipment (
        ShipmentFactKey BIGINT IDENTITY(1,1) PRIMARY KEY,
        ShipmentID NVARCHAR(60) NOT NULL,
        PurchaseOrderID NVARCHAR(60) NOT NULL,
        OrderDateKey INT NOT NULL,
        PromisedDateKey INT NOT NULL,
        DeliveryDateKey INT NULL,
        SupplierKey INT NOT NULL,
        StoreKey INT NOT NULL,
        ProductKey INT NOT NULL,
        -- Measures
        QuantityOrdered INT NOT NULL,
        QuantityReceived INT NOT NULL,
        LeadTimeDays INT NOT NULL,
        DaysDelayed INT NOT NULL DEFAULT 0,
        OnTimeDeliveryFlag BIT NOT NULL DEFAULT 1, -- 1 if DeliveryDate <= PromisedDate
        FullOrderFillFlag BIT NOT NULL DEFAULT 1,  -- 1 if QuantityReceived >= QuantityOrdered
        -- Audit
        ETLRunID INT NOT NULL DEFAULT 1,
        CreatedTimestamp DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
GO

PRINT 'Fact tables created in dw schema successfully.';
GO
