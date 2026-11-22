-- ============================================================================
-- Script: 02_create_source_tables.sql
-- Description: Creates operational source ingestion tables in [raw] and
--              audit logging tables in [audit].
-- ============================================================================

USE [RetailIntelligenceDW];
GO

-- ----------------------------------------------------------------------------
-- 1. Audit & Pipeline Execution Tracking
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'audit.ETLRunHistory', N'U') IS NULL
BEGIN
    CREATE TABLE audit.ETLRunHistory (
        ETLRunID INT IDENTITY(1,1) PRIMARY KEY,
        PipelineName NVARCHAR(100) NOT NULL,
        ExecutionMode NVARCHAR(50) NOT NULL DEFAULT 'FULL',
        StartTime DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
        EndTime DATETIME2(3) NULL,
        Status NVARCHAR(30) NOT NULL DEFAULT 'RUNNING', -- RUNNING, SUCCESS, FAILED
        SourceRowCount INT NOT NULL DEFAULT 0,
        InsertedRowCount INT NOT NULL DEFAULT 0,
        UpdatedRowCount INT NOT NULL DEFAULT 0,
        RejectedRowCount INT NOT NULL DEFAULT 0,
        ErrorMessage NVARCHAR(MAX) NULL
    );
END;
GO

IF OBJECT_ID(N'audit.DataQualityLog', N'U') IS NULL
BEGIN
    CREATE TABLE audit.DataQualityLog (
        LogID INT IDENTITY(1,1) PRIMARY KEY,
        ETLRunID INT NULL,
        CheckTimestamp DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
        TableName NVARCHAR(100) NOT NULL,
        CheckType NVARCHAR(50) NOT NULL, -- NULL_CHECK, REFERENTIAL_INTEGRITY, RANGE_CHECK, DUPLICATE_CHECK
        CheckDescription NVARCHAR(255) NOT NULL,
        RecordsFailed INT NOT NULL DEFAULT 0,
        Severity NVARCHAR(20) NOT NULL DEFAULT 'WARNING', -- WARNING, ERROR, CRITICAL
        Status NVARCHAR(20) NOT NULL DEFAULT 'PASSED'     -- PASSED, FAILED
    );
END;
GO

-- ----------------------------------------------------------------------------
-- 2. Raw Ingestion Tables (Source Data Layer)
-- ----------------------------------------------------------------------------

IF OBJECT_ID(N'raw.SourceCalendar', N'U') IS NULL
BEGIN
    CREATE TABLE raw.SourceCalendar (
        CalendarDate DATE PRIMARY KEY,
        DayOfWeek INT NOT NULL,
        DayName NVARCHAR(20) NOT NULL,
        DayOfMonth INT NOT NULL,
        DayOfYear INT NOT NULL,
        WeekNumber INT NOT NULL,
        MonthNumber INT NOT NULL,
        MonthName NVARCHAR(20) NOT NULL,
        QuarterNumber INT NOT NULL,
        YearNumber INT NOT NULL,
        IsWeekend BIT NOT NULL,
        IsHoliday BIT NOT NULL,
        HolidayName NVARCHAR(100) NULL,
        Season NVARCHAR(20) NOT NULL
    );
END;
GO

IF OBJECT_ID(N'raw.SourceProduct', N'U') IS NULL
BEGIN
    CREATE TABLE raw.SourceProduct (
        SourceProductID NVARCHAR(50) NOT NULL,
        ProductName NVARCHAR(200) NOT NULL,
        Category NVARCHAR(100) NOT NULL,
        Subcategory NVARCHAR(100) NOT NULL,
        Brand NVARCHAR(100) NOT NULL,
        UnitCost DECIMAL(12, 4) NOT NULL,
        BasePrice DECIMAL(12, 4) NOT NULL,
        UnitOfMeasure NVARCHAR(30) NOT NULL DEFAULT 'EACH',
        SourceSupplierID NVARCHAR(50) NULL,
        CreatedDate DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        ModifiedDate DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
GO

IF OBJECT_ID(N'raw.SourceStore', N'U') IS NULL
BEGIN
    CREATE TABLE raw.SourceStore (
        SourceStoreID NVARCHAR(50) NOT NULL,
        StoreName NVARCHAR(150) NOT NULL,
        StoreType NVARCHAR(50) NOT NULL, -- Supercenter, Neighborhood Market, Discount Store, Express
        AddressLine NVARCHAR(255) NULL,
        City NVARCHAR(100) NOT NULL,
        StateOrRegion NVARCHAR(50) NOT NULL,
        PostalCode NVARCHAR(20) NULL,
        Country NVARCHAR(50) NOT NULL DEFAULT 'USA',
        SquareFootage INT NOT NULL,
        OpenDate DATE NOT NULL
    );
END;
GO

IF OBJECT_ID(N'raw.SourceCustomer', N'U') IS NULL
BEGIN
    CREATE TABLE raw.SourceCustomer (
        SourceCustomerID NVARCHAR(50) NOT NULL,
        CustomerName NVARCHAR(150) NOT NULL,
        Email NVARCHAR(255) NULL,
        CustomerSegment NVARCHAR(50) NOT NULL, -- Premium, Regular, Value, Occasional
        City NVARCHAR(100) NOT NULL,
        StateOrRegion NVARCHAR(50) NOT NULL,
        JoinDate DATE NOT NULL
    );
END;
GO

IF OBJECT_ID(N'raw.SourceSupplier', N'U') IS NULL
BEGIN
    CREATE TABLE raw.SourceSupplier (
        SourceSupplierID NVARCHAR(50) NOT NULL,
        SupplierName NVARCHAR(150) NOT NULL,
        SupplierCategory NVARCHAR(100) NOT NULL,
        Country NVARCHAR(50) NOT NULL DEFAULT 'USA',
        Region NVARCHAR(50) NOT NULL,
        LeadTimeDays INT NOT NULL DEFAULT 7,
        QualityRating DECIMAL(4, 2) NOT NULL DEFAULT 4.5
    );
END;
GO

IF OBJECT_ID(N'raw.SourcePromotion', N'U') IS NULL
BEGIN
    CREATE TABLE raw.SourcePromotion (
        PromotionID NVARCHAR(50) NOT NULL,
        PromotionName NVARCHAR(150) NOT NULL,
        PromotionType NVARCHAR(50) NOT NULL, -- Holiday Special, Flash Sale, Rollback, Clearance
        DiscountPercent DECIMAL(5, 2) NOT NULL,
        StartDate DATE NOT NULL,
        EndDate DATE NOT NULL
    );
END;
GO

IF OBJECT_ID(N'raw.SourceSalesTransaction', N'U') IS NULL
BEGIN
    CREATE TABLE raw.SourceSalesTransaction (
        TransactionID NVARCHAR(60) NOT NULL,
        SourceStoreID NVARCHAR(50) NOT NULL,
        SourceCustomerID NVARCHAR(50) NULL,
        TransactionDate DATE NOT NULL,
        TransactionTime TIME(0) NOT NULL,
        Channel NVARCHAR(30) NOT NULL DEFAULT 'In-Store', -- In-Store, Online, Mobile, Curbside
        TotalAmount DECIMAL(14, 4) NOT NULL,
        PaymentMethod NVARCHAR(40) NOT NULL DEFAULT 'Credit Card'
    );
END;
GO

IF OBJECT_ID(N'raw.SourceSalesTransactionLine', N'U') IS NULL
BEGIN
    CREATE TABLE raw.SourceSalesTransactionLine (
        TransactionID NVARCHAR(60) NOT NULL,
        LineNumber INT NOT NULL,
        SourceProductID NVARCHAR(50) NOT NULL,
        Quantity INT NOT NULL,
        UnitPrice DECIMAL(12, 4) NOT NULL,
        DiscountAmount DECIMAL(12, 4) NOT NULL DEFAULT 0.0000,
        LineTotalAmount DECIMAL(14, 4) NOT NULL,
        PromotionID NVARCHAR(50) NULL
    );
END;
GO

IF OBJECT_ID(N'raw.SourceInventory', N'U') IS NULL
BEGIN
    CREATE TABLE raw.SourceInventory (
        SnapshotDate DATE NOT NULL,
        SourceStoreID NVARCHAR(50) NOT NULL,
        SourceProductID NVARCHAR(50) NOT NULL,
        QuantityOnHand INT NOT NULL,
        QuantityOnOrder INT NOT NULL DEFAULT 0,
        ReorderPoint INT NOT NULL,
        SafetyStock INT NOT NULL
    );
END;
GO

IF OBJECT_ID(N'raw.SourceShipment', N'U') IS NULL
BEGIN
    CREATE TABLE raw.SourceShipment (
        ShipmentID NVARCHAR(60) NOT NULL,
        PurchaseOrderID NVARCHAR(60) NOT NULL,
        SourceSupplierID NVARCHAR(50) NOT NULL,
        SourceStoreID NVARCHAR(50) NOT NULL,
        SourceProductID NVARCHAR(50) NOT NULL,
        OrderDate DATE NOT NULL,
        PromisedDeliveryDate DATE NOT NULL,
        ActualDeliveryDate DATE NULL,
        QuantityOrdered INT NOT NULL,
        QuantityReceived INT NOT NULL,
        ShipmentStatus NVARCHAR(30) NOT NULL -- Delivered, In-Transit, Delayed, Cancelled
    );
END;
GO

PRINT 'Source tables created in raw schema successfully.';
GO
