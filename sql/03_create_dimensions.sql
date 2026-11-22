-- ============================================================================
-- Script: 03_create_dimensions.sql
-- Description: Creates conformed dimension tables in the [dw] schema with
--              surrogate keys, SCD Type 1 & 2 support, and default unknown rows.
-- ============================================================================

USE [RetailIntelligenceDW];
GO

-- ----------------------------------------------------------------------------
-- 1. DimDate
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.DimDate', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimDate (
        DateKey INT NOT NULL PRIMARY KEY, -- Format: YYYYMMDD
        FullDate DATE NOT NULL UNIQUE,
        DayOfWeek INT NOT NULL,
        DayName NVARCHAR(20) NOT NULL,
        DayOfMonth INT NOT NULL,
        DayOfYear INT NOT NULL,
        WeekNumber INT NOT NULL,
        MonthNumber INT NOT NULL,
        MonthName NVARCHAR(20) NOT NULL,
        QuarterNumber INT NOT NULL,
        YearNumber INT NOT NULL,
        WeekendFlag BIT NOT NULL,
        HolidayFlag BIT NOT NULL,
        HolidayName NVARCHAR(100) NULL,
        Season NVARCHAR(20) NOT NULL,
        FiscalYear INT NOT NULL,
        FiscalQuarter INT NOT NULL
    );
END;
GO

-- ----------------------------------------------------------------------------
-- 2. DimProduct (SCD Type 2 Enabled)
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.DimProduct', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimProduct (
        ProductKey INT IDENTITY(1,1) PRIMARY KEY,
        SourceProductID NVARCHAR(50) NOT NULL,
        ProductName NVARCHAR(200) NOT NULL,
        Category NVARCHAR(100) NOT NULL,
        Subcategory NVARCHAR(100) NOT NULL,
        Brand NVARCHAR(100) NOT NULL,
        UnitCost DECIMAL(12, 4) NOT NULL,
        BasePrice DECIMAL(12, 4) NOT NULL,
        UnitOfMeasure NVARCHAR(30) NOT NULL DEFAULT 'EACH',
        SourceSupplierID NVARCHAR(50) NULL,
        EffectiveFrom DATETIME2(0) NOT NULL,
        EffectiveTo DATETIME2(0) NULL,
        IsCurrent BIT NOT NULL DEFAULT 1,
        VersionNumber INT NOT NULL DEFAULT 1
    );
END;
GO

-- ----------------------------------------------------------------------------
-- 3. DimStore (SCD Type 1 & 2 Support)
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.DimStore', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimStore (
        StoreKey INT IDENTITY(1,1) PRIMARY KEY,
        SourceStoreID NVARCHAR(50) NOT NULL,
        StoreName NVARCHAR(150) NOT NULL,
        StoreType NVARCHAR(50) NOT NULL,
        AddressLine NVARCHAR(255) NULL,
        City NVARCHAR(100) NOT NULL,
        StateOrRegion NVARCHAR(50) NOT NULL,
        PostalCode NVARCHAR(20) NULL,
        Country NVARCHAR(50) NOT NULL DEFAULT 'USA',
        SquareFootage INT NOT NULL,
        OpenDate DATE NOT NULL,
        EffectiveFrom DATETIME2(0) NOT NULL,
        EffectiveTo DATETIME2(0) NULL,
        IsCurrent BIT NOT NULL DEFAULT 1
    );
END;
GO

-- ----------------------------------------------------------------------------
-- 4. DimCustomer (SCD Type 2 Support)
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.DimCustomer', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimCustomer (
        CustomerKey INT IDENTITY(1,1) PRIMARY KEY,
        SourceCustomerID NVARCHAR(50) NOT NULL,
        CustomerName NVARCHAR(150) NOT NULL,
        CustomerSegment NVARCHAR(50) NOT NULL,
        City NVARCHAR(100) NOT NULL,
        StateOrRegion NVARCHAR(50) NOT NULL,
        JoinDate DATE NOT NULL,
        EffectiveFrom DATETIME2(0) NOT NULL,
        EffectiveTo DATETIME2(0) NULL,
        IsCurrent BIT NOT NULL DEFAULT 1
    );
END;
GO

-- ----------------------------------------------------------------------------
-- 5. DimChannel
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.DimChannel', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimChannel (
        ChannelKey INT IDENTITY(1,1) PRIMARY KEY,
        ChannelName NVARCHAR(50) NOT NULL UNIQUE,
        ChannelDescription NVARCHAR(200) NULL
    );
END;
GO

-- ----------------------------------------------------------------------------
-- 6. DimPromotion
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.DimPromotion', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimPromotion (
        PromotionKey INT IDENTITY(1,1) PRIMARY KEY,
        PromotionID NVARCHAR(50) NOT NULL,
        PromotionName NVARCHAR(150) NOT NULL,
        PromotionType NVARCHAR(50) NOT NULL,
        DiscountPercent DECIMAL(5, 2) NOT NULL,
        StartDate DATE NOT NULL,
        EndDate DATE NOT NULL
    );
END;
GO

-- ----------------------------------------------------------------------------
-- 7. DimSupplier
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.DimSupplier', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimSupplier (
        SupplierKey INT IDENTITY(1,1) PRIMARY KEY,
        SourceSupplierID NVARCHAR(50) NOT NULL,
        SupplierName NVARCHAR(150) NOT NULL,
        SupplierCategory NVARCHAR(100) NOT NULL,
        Region NVARCHAR(50) NOT NULL,
        Country NVARCHAR(50) NOT NULL DEFAULT 'USA',
        StandardLeadTimeDays INT NOT NULL DEFAULT 7,
        QualityRating DECIMAL(4, 2) NOT NULL DEFAULT 4.5
    );
END;
GO

-- ----------------------------------------------------------------------------
-- Seed Standard Default Records for Unmatched / Late-Arriving Records
-- ----------------------------------------------------------------------------

-- Default Promotion (No Promotion)
SET IDENTITY_INSERT dw.DimPromotion ON;
IF NOT EXISTS (SELECT 1 FROM dw.DimPromotion WHERE PromotionKey = 0)
BEGIN
    INSERT INTO dw.DimPromotion (PromotionKey, PromotionID, PromotionName, PromotionType, DiscountPercent, StartDate, EndDate)
    VALUES (0, 'PROMO-NONE', 'No Promotion', 'Standard Everyday Low Price', 0.00, '2000-01-01', '2099-12-31');
END;
SET IDENTITY_INSERT dw.DimPromotion OFF;
GO

-- Default Channel (In-Store / Standard)
SET IDENTITY_INSERT dw.DimChannel ON;
IF NOT EXISTS (SELECT 1 FROM dw.DimChannel WHERE ChannelKey = 0)
BEGIN
    INSERT INTO dw.DimChannel (ChannelKey, ChannelName, ChannelDescription)
    VALUES (0, 'Unknown / Default', 'Fallback channel for unclassified sales');
END;
SET IDENTITY_INSERT dw.DimChannel OFF;
GO

PRINT 'Dimension tables created in dw schema successfully.';
GO
