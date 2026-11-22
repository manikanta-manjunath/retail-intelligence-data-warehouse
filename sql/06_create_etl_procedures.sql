-- ============================================================================
-- Script: 06_create_etl_procedures.sql
-- Description: Stored procedures for ETL pipeline orchestration, SCD Type 1 & 2
--              dimension loads, fact loading, and audit logging.
-- ============================================================================

USE [RetailIntelligenceDW];
GO

-- ----------------------------------------------------------------------------
-- 1. Audit Procedures
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE audit.usp_StartETLRun
    @PipelineName NVARCHAR(100),
    @ExecutionMode NVARCHAR(50),
    @ETLRunID INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    INSERT INTO audit.ETLRunHistory (PipelineName, ExecutionMode, StartTime, Status)
    VALUES (@PipelineName, @ExecutionMode, SYSUTCDATETIME(), 'RUNNING');

    SET @ETLRunID = SCOPE_IDENTITY();
END;
GO

CREATE OR ALTER PROCEDURE audit.usp_EndETLRun
    @ETLRunID INT,
    @Status NVARCHAR(30),
    @SourceRowCount INT,
    @InsertedRowCount INT,
    @UpdatedRowCount INT,
    @RejectedRowCount INT,
    @ErrorMessage NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    UPDATE audit.ETLRunHistory
    SET EndTime = SYSUTCDATETIME(),
        Status = @Status,
        SourceRowCount = @SourceRowCount,
        InsertedRowCount = @InsertedRowCount,
        UpdatedRowCount = @UpdatedRowCount,
        RejectedRowCount = @RejectedRowCount,
        ErrorMessage = @ErrorMessage
    WHERE ETLRunID = @ETLRunID;
END;
GO

-- ----------------------------------------------------------------------------
-- 2. Dimension Loading: DimDate
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dw.usp_LoadDimDate
    @ETLRunID INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRY
        INSERT INTO dw.DimDate (
            DateKey, FullDate, DayOfWeek, DayName, DayOfMonth, DayOfYear,
            WeekNumber, MonthNumber, MonthName, QuarterNumber, YearNumber,
            WeekendFlag, HolidayFlag, HolidayName, Season, FiscalYear, FiscalQuarter
        )
        SELECT
            CAST(CONVERT(VARCHAR(8), c.CalendarDate, 112) AS INT) AS DateKey,
            c.CalendarDate,
            c.DayOfWeek,
            c.DayName,
            c.DayOfMonth,
            c.DayOfYear,
            c.WeekNumber,
            c.MonthNumber,
            c.MonthName,
            c.QuarterNumber,
            c.YearNumber,
            c.IsWeekend,
            c.IsHoliday,
            c.HolidayName,
            c.Season,
            c.YearNumber AS FiscalYear,
            c.QuarterNumber AS FiscalQuarter
        FROM (SELECT * FROM stg.SourceCalendar WHERE ETLRunID = @ETLRunID) c
        WHERE NOT EXISTS (
            SELECT 1 FROM dw.DimDate d
            WHERE d.DateKey = CAST(CONVERT(VARCHAR(8), c.CalendarDate, 112) AS INT)
        );

        PRINT 'dw.DimDate loaded successfully.';
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH;
END;
GO

-- ----------------------------------------------------------------------------
-- 3. Dimension Loading: DimProduct (SCD Type 2 Implementation)
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dw.usp_LoadDimProduct_SCD2
    @ETLRunID INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @Now DATETIME2(0) = SYSUTCDATETIME();

    BEGIN TRANSACTION;
    BEGIN TRY
        -- Step A: Detect attribute changes for existing current products (SCD Type 2 expiry)
        UPDATE dp
        SET dp.EffectiveTo = sp.ModifiedDate,
            dp.IsCurrent = 0
        FROM dw.DimProduct dp
        INNER JOIN (SELECT * FROM stg.SourceProduct WHERE ETLRunID = @ETLRunID) sp ON dp.SourceProductID = sp.SourceProductID
        WHERE dp.IsCurrent = 1
          AND (
               dp.BasePrice <> sp.BasePrice
            OR dp.UnitCost <> sp.UnitCost
            OR dp.Category <> sp.Category
            OR dp.Subcategory <> sp.Subcategory
            OR dp.ProductName <> sp.ProductName OR dp.Brand <> sp.Brand
            OR dp.UnitOfMeasure <> sp.UnitOfMeasure
            OR ISNULL(dp.SourceSupplierID,'') <> ISNULL(sp.SourceSupplierID,'')
          );

        -- Step B: Insert new versions for updated records or brand new products
        INSERT INTO dw.DimProduct (
            SourceProductID, ProductName, Category, Subcategory, Brand,
            UnitCost, BasePrice, UnitOfMeasure, SourceSupplierID,
            EffectiveFrom, EffectiveTo, IsCurrent, VersionNumber
        )
        SELECT
            sp.SourceProductID,
            sp.ProductName,
            sp.Category,
            sp.Subcategory,
            sp.Brand,
            sp.UnitCost,
            sp.BasePrice,
            sp.UnitOfMeasure,
            sp.SourceSupplierID,
            CASE WHEN prev.MaxVersion IS NULL THEN CAST('1900-01-01' AS DATETIME2(0)) ELSE sp.ModifiedDate END AS EffectiveFrom,
            NULL AS EffectiveTo,
            1 AS IsCurrent,
            ISNULL(prev.MaxVersion, 0) + 1 AS VersionNumber
        FROM (SELECT * FROM stg.SourceProduct WHERE ETLRunID = @ETLRunID) sp
        OUTER APPLY (
            SELECT MAX(VersionNumber) AS MaxVersion
            FROM dw.DimProduct p
            WHERE p.SourceProductID = sp.SourceProductID
        ) prev
        WHERE NOT EXISTS (
            SELECT 1 FROM dw.DimProduct curr
            WHERE curr.SourceProductID = sp.SourceProductID
              AND curr.IsCurrent = 1
              AND curr.BasePrice = sp.BasePrice
              AND curr.UnitCost = sp.UnitCost
              AND curr.Category = sp.Category
              AND curr.Subcategory = sp.Subcategory
              AND curr.ProductName = sp.ProductName AND curr.Brand = sp.Brand
              AND curr.UnitOfMeasure = sp.UnitOfMeasure
              AND ISNULL(curr.SourceSupplierID,'') = ISNULL(sp.SourceSupplierID,'')
        );

        COMMIT TRANSACTION;
        PRINT 'dw.DimProduct (SCD Type 2) synchronized successfully.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- ----------------------------------------------------------------------------
-- 4. Dimension Loading: DimStore (SCD Type 1 - Overwrite in-place)
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dw.usp_LoadDimStore_SCD1
    @ETLRunID INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @Now DATETIME2(0) = SYSUTCDATETIME();

    BEGIN TRANSACTION;
    BEGIN TRY
        -- Update existing stores in place (SCD Type 1)
        UPDATE ds
        SET ds.StoreName = ss.StoreName,
            ds.StoreType = ss.StoreType,
            ds.AddressLine = ss.AddressLine,
            ds.City = ss.City,
            ds.StateOrRegion = ss.StateOrRegion,
            ds.PostalCode = ss.PostalCode,
            ds.SquareFootage = ss.SquareFootage, ds.Country = ss.Country, ds.OpenDate = ss.OpenDate
        FROM dw.DimStore ds
        INNER JOIN (SELECT * FROM stg.SourceStore WHERE ETLRunID = @ETLRunID) ss ON ds.SourceStoreID = ss.SourceStoreID;

        -- Insert new stores
        INSERT INTO dw.DimStore (
            SourceStoreID, StoreName, StoreType, AddressLine, City,
            StateOrRegion, PostalCode, Country, SquareFootage, OpenDate,
            EffectiveFrom, EffectiveTo, IsCurrent
        )
        SELECT
            ss.SourceStoreID, ss.StoreName, ss.StoreType, ss.AddressLine, ss.City,
            ss.StateOrRegion, ss.PostalCode, ss.Country, ss.SquareFootage, ss.OpenDate,
            @Now, NULL, 1
        FROM (SELECT * FROM stg.SourceStore WHERE ETLRunID = @ETLRunID) ss
        WHERE NOT EXISTS (
            SELECT 1 FROM dw.DimStore ds WHERE ds.SourceStoreID = ss.SourceStoreID
        );

        COMMIT TRANSACTION;
        PRINT 'dw.DimStore (SCD Type 1) loaded successfully.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- ----------------------------------------------------------------------------
-- 5. Dimension Loading: DimCustomer
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dw.usp_LoadDimCustomer
    @ETLRunID INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @Now DATETIME2(0) = SYSUTCDATETIME();

    BEGIN TRANSACTION;
    BEGIN TRY
        UPDATE dc
        SET dc.CustomerName = sc.CustomerName,
            dc.CustomerSegment = sc.CustomerSegment,
            dc.City = sc.City,
            dc.StateOrRegion = sc.StateOrRegion,
            dc.JoinDate = sc.JoinDate
        FROM dw.DimCustomer dc
        INNER JOIN (SELECT * FROM stg.SourceCustomer WHERE ETLRunID = @ETLRunID) sc ON dc.SourceCustomerID = sc.SourceCustomerID;

        INSERT INTO dw.DimCustomer (
            SourceCustomerID, CustomerName, CustomerSegment, City,
            StateOrRegion, JoinDate, EffectiveFrom, EffectiveTo, IsCurrent
        )
        SELECT
            sc.SourceCustomerID, sc.CustomerName, sc.CustomerSegment, sc.City,
            sc.StateOrRegion, sc.JoinDate, @Now, NULL, 1
        FROM (SELECT * FROM stg.SourceCustomer WHERE ETLRunID = @ETLRunID) sc
        WHERE NOT EXISTS (
            SELECT 1 FROM dw.DimCustomer dc WHERE dc.SourceCustomerID = sc.SourceCustomerID
        );

        COMMIT TRANSACTION;
        PRINT 'dw.DimCustomer loaded successfully.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- ----------------------------------------------------------------------------
-- 6. Dimension Loading: DimChannel, DimPromotion, DimSupplier
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dw.usp_LoadDimAuxiliary
    @ETLRunID INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRY
        -- Channels
        INSERT INTO dw.DimChannel (ChannelName, ChannelDescription)
        SELECT DISTINCT Channel, 'Retail sales channel: ' + Channel
        FROM (SELECT * FROM stg.SourceSalesTransaction WHERE ETLRunID = @ETLRunID) tx
        WHERE Channel IS NOT NULL
          AND Channel NOT IN (SELECT ChannelName FROM dw.DimChannel);

        -- Type 1 updates for reference attributes. Product costs remain SCD2.
        UPDATE dp SET PromotionName=sp.PromotionName, PromotionType=sp.PromotionType,
            DiscountPercent=sp.DiscountPercent, StartDate=sp.StartDate, EndDate=sp.EndDate
        FROM dw.DimPromotion dp JOIN stg.SourcePromotion sp ON dp.PromotionID=sp.PromotionID
        WHERE sp.ETLRunID=@ETLRunID;
        UPDATE ds SET SupplierName=ss.SupplierName, SupplierCategory=ss.SupplierCategory,
            Region=ss.Region, Country=ss.Country, StandardLeadTimeDays=ss.LeadTimeDays, QualityRating=ss.QualityRating
        FROM dw.DimSupplier ds JOIN stg.SourceSupplier ss ON ds.SourceSupplierID=ss.SourceSupplierID
        WHERE ss.ETLRunID=@ETLRunID;

        -- Promotions
        INSERT INTO dw.DimPromotion (PromotionID, PromotionName, PromotionType, DiscountPercent, StartDate, EndDate)
        SELECT sp.PromotionID, sp.PromotionName, sp.PromotionType, sp.DiscountPercent, sp.StartDate, sp.EndDate
        FROM (SELECT * FROM stg.SourcePromotion WHERE ETLRunID = @ETLRunID) sp
        WHERE NOT EXISTS (SELECT 1 FROM dw.DimPromotion dp WHERE dp.PromotionID = sp.PromotionID);

        -- Suppliers
        INSERT INTO dw.DimSupplier (SourceSupplierID, SupplierName, SupplierCategory, Region, Country, StandardLeadTimeDays, QualityRating)
        SELECT ss.SourceSupplierID, ss.SupplierName, ss.SupplierCategory, ss.Region, ss.Country, ss.LeadTimeDays, ss.QualityRating
        FROM (SELECT * FROM stg.SourceSupplier WHERE ETLRunID = @ETLRunID) ss
        WHERE NOT EXISTS (SELECT 1 FROM dw.DimSupplier ds WHERE ds.SourceSupplierID = ss.SourceSupplierID);

        PRINT 'Auxiliary dimensions (Channel, Promotion, Supplier) loaded successfully.';
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH;
END;
GO

-- ----------------------------------------------------------------------------
-- 7. Fact Loading: FactSales (Idempotent, surrogate resolution, audit-tagged)
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dw.usp_LoadFactSales
    @ETLRunID INT,
    @InsertedCount INT OUTPUT,
    @SourceSystem NVARCHAR(50) = 'SYNTHETIC_CANONICAL'
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    SET @InsertedCount = 0;

    BEGIN TRANSACTION;
    BEGIN TRY
        -- Staging CTE resolving surrogate keys
        ;WITH StagedSales AS (
            SELECT
                stl.TransactionID,
                stl.LineNumber AS TransactionLineID,
                CAST(CONVERT(VARCHAR(8), st.TransactionDate, 112) AS INT) AS DateKey,
                ISNULL(dp.ProductKey, -1) AS ProductKey,
                ISNULL(ds.StoreKey, -1) AS StoreKey,
                ISNULL(dc.ChannelKey, 0) AS ChannelKey,
                ISNULL(dprom.PromotionKey, 0) AS PromotionKey,
                cust.CustomerKey AS CustomerKey,
                stl.Quantity AS QuantitySold,
                stl.UnitPrice,
                CAST(stl.Quantity * stl.UnitPrice AS DECIMAL(14,4)) AS GrossSalesAmount,
                stl.DiscountAmount,
                CAST((stl.Quantity * stl.UnitPrice) - stl.DiscountAmount AS DECIMAL(14,4)) AS NetSalesAmount,
                CAST(stl.Quantity * dp.UnitCost AS DECIMAL(14,4)) AS CostAmount,
                CAST(((stl.Quantity * stl.UnitPrice) - stl.DiscountAmount) - (stl.Quantity * dp.UnitCost) AS DECIMAL(14,4)) AS ProfitAmount
            FROM (SELECT * FROM stg.SourceSalesTransactionLine WHERE ETLRunID = @ETLRunID) stl
            INNER JOIN (SELECT * FROM stg.SourceSalesTransaction WHERE ETLRunID = @ETLRunID) st ON stl.TransactionID = st.TransactionID
            -- Resolve Product surrogate key (active at transaction date)
            LEFT JOIN dw.DimProduct dp
                ON dp.SourceProductID = stl.SourceProductID
               AND DATEADD(SECOND,DATEDIFF(SECOND,CAST('00:00:00' AS TIME),st.TransactionTime),CAST(st.TransactionDate AS DATETIME2(0))) >= dp.EffectiveFrom
               AND (dp.EffectiveTo IS NULL OR DATEADD(SECOND,DATEDIFF(SECOND,CAST('00:00:00' AS TIME),st.TransactionTime),CAST(st.TransactionDate AS DATETIME2(0))) < dp.EffectiveTo)
            -- Resolve Store surrogate key
            LEFT JOIN dw.DimStore ds
                ON ds.SourceStoreID = st.SourceStoreID
               AND ds.IsCurrent = 1
            -- Resolve Channel
            LEFT JOIN dw.DimChannel dc
                ON dc.ChannelName = st.Channel
            -- Resolve Promotion
            LEFT JOIN dw.DimPromotion dprom
                ON dprom.PromotionID = stl.PromotionID
            -- Resolve Customer
            LEFT JOIN dw.DimCustomer cust
                ON cust.SourceCustomerID = st.SourceCustomerID
               AND cust.IsCurrent = 1
            -- Filter out previously loaded records for idempotency
            WHERE NOT EXISTS (
                SELECT 1 FROM dw.FactSales fs
                WHERE fs.TransactionID = stl.TransactionID
                  AND fs.TransactionLineID = stl.LineNumber
            )
        )
        INSERT INTO dw.FactSales (
            TransactionID, TransactionLineID, DateKey, ProductKey,
            StoreKey, ChannelKey, PromotionKey, CustomerKey,
            QuantitySold, UnitPrice, GrossSalesAmount, DiscountAmount,
            NetSalesAmount, CostAmount, ProfitAmount, SourceSystem, ETLRunID
        )
        SELECT
            TransactionID, TransactionLineID, DateKey, ProductKey,
            StoreKey, ChannelKey, PromotionKey, CustomerKey,
            QuantitySold, UnitPrice, GrossSalesAmount, DiscountAmount,
            NetSalesAmount, CostAmount, ProfitAmount, @SourceSystem, @ETLRunID
        FROM StagedSales
        WHERE ProductKey <> -1 AND StoreKey <> -1; -- Guard referential integrity

        SET @InsertedCount = @@ROWCOUNT;

        COMMIT TRANSACTION;
        PRINT 'dw.FactSales loaded: ' + CAST(@InsertedCount AS VARCHAR(20)) + ' records.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- ----------------------------------------------------------------------------
-- 8. Fact Loading: FactInventorySnapshot
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dw.usp_LoadFactInventorySnapshot
    @ETLRunID INT,
    @InsertedCount INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    SET @InsertedCount = 0;

    BEGIN TRANSACTION;
    BEGIN TRY
        ;WITH StagedInventory AS (
            SELECT
                CAST(CONVERT(VARCHAR(8), si.SnapshotDate, 112) AS INT) AS DateKey,
                dp.ProductKey,
                ds.StoreKey,
                si.QuantityOnHand,
                si.QuantityOnOrder,
                si.ReorderPoint,
                si.SafetyStock,
                dp.UnitCost,
                CAST(si.QuantityOnHand * dp.UnitCost AS DECIMAL(16,4)) AS InventoryValue,
                CASE WHEN si.QuantityOnHand <= 0 THEN 1 ELSE 0 END AS StockoutFlag,
                CASE WHEN si.QuantityOnHand < si.ReorderPoint THEN 1 ELSE 0 END AS UnderStockFlag,
                CASE WHEN si.QuantityOnHand > (si.ReorderPoint * 3) THEN 1 ELSE 0 END AS OverStockFlag
            FROM (SELECT * FROM stg.SourceInventory WHERE ETLRunID = @ETLRunID) si
            INNER JOIN dw.DimProduct dp ON dp.SourceProductID = si.SourceProductID
                AND si.SnapshotDate >= dp.EffectiveFrom AND (dp.EffectiveTo IS NULL OR si.SnapshotDate < dp.EffectiveTo)
            INNER JOIN dw.DimStore ds ON ds.SourceStoreID = si.SourceStoreID AND ds.IsCurrent = 1
            WHERE NOT EXISTS (
                SELECT 1 FROM dw.FactInventorySnapshot fis
                WHERE fis.DateKey = CAST(CONVERT(VARCHAR(8), si.SnapshotDate, 112) AS INT)
                  AND fis.ProductKey = dp.ProductKey
                  AND fis.StoreKey = ds.StoreKey
            )
        )
        INSERT INTO dw.FactInventorySnapshot (
            DateKey, ProductKey, StoreKey, QuantityOnHand, QuantityOnOrder,
            ReorderPoint, SafetyStock, UnitCost, InventoryValue,
            StockoutFlag, UnderStockFlag, OverStockFlag, ETLRunID
        )
        SELECT
            DateKey, ProductKey, StoreKey, QuantityOnHand, QuantityOnOrder,
            ReorderPoint, SafetyStock, UnitCost, InventoryValue,
            StockoutFlag, UnderStockFlag, OverStockFlag, @ETLRunID
        FROM StagedInventory;

        SET @InsertedCount = @@ROWCOUNT;

        COMMIT TRANSACTION;
        PRINT 'dw.FactInventorySnapshot loaded: ' + CAST(@InsertedCount AS VARCHAR(20)) + ' records.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- ----------------------------------------------------------------------------
-- 9. Fact Loading: FactShipment
-- ----------------------------------------------------------------------------
CREATE OR ALTER PROCEDURE dw.usp_LoadFactShipment
    @ETLRunID INT,
    @InsertedCount INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    SET @InsertedCount = 0;

    BEGIN TRANSACTION;
    BEGIN TRY
        ;WITH StagedShipments AS (
            SELECT
                ss.ShipmentID,
                ss.PurchaseOrderID,
                CAST(CONVERT(VARCHAR(8), ss.OrderDate, 112) AS INT) AS OrderDateKey,
                CAST(CONVERT(VARCHAR(8), ss.PromisedDeliveryDate, 112) AS INT) AS PromisedDateKey,
                CASE WHEN ss.ActualDeliveryDate IS NOT NULL
                     THEN CAST(CONVERT(VARCHAR(8), ss.ActualDeliveryDate, 112) AS INT)
                     ELSE NULL END AS DeliveryDateKey,
                dsupp.SupplierKey,
                dstore.StoreKey,
                dp.ProductKey,
                ss.QuantityOrdered,
                ss.QuantityReceived,
                DATEDIFF(DAY, ss.OrderDate, ISNULL(ss.ActualDeliveryDate, ss.PromisedDeliveryDate)) AS LeadTimeDays,
                CASE WHEN ss.ActualDeliveryDate > ss.PromisedDeliveryDate
                     THEN DATEDIFF(DAY, ss.PromisedDeliveryDate, ss.ActualDeliveryDate)
                     ELSE 0 END AS DaysDelayed,
                CASE WHEN ss.ActualDeliveryDate <= ss.PromisedDeliveryDate THEN 1 ELSE 0 END AS OnTimeDeliveryFlag,
                CASE WHEN ss.QuantityReceived >= ss.QuantityOrdered THEN 1 ELSE 0 END AS FullOrderFillFlag
            FROM (SELECT * FROM stg.SourceShipment WHERE ETLRunID = @ETLRunID) ss
            INNER JOIN dw.DimSupplier dsupp ON dsupp.SourceSupplierID = ss.SourceSupplierID
            INNER JOIN dw.DimStore dstore ON dstore.SourceStoreID = ss.SourceStoreID AND dstore.IsCurrent = 1
            INNER JOIN dw.DimProduct dp ON dp.SourceProductID = ss.SourceProductID
                AND ss.OrderDate >= dp.EffectiveFrom AND (dp.EffectiveTo IS NULL OR ss.OrderDate < dp.EffectiveTo)
            WHERE NOT EXISTS (
                SELECT 1 FROM dw.FactShipment fs WHERE fs.ShipmentID = ss.ShipmentID
            )
        )
        INSERT INTO dw.FactShipment (
            ShipmentID, PurchaseOrderID, OrderDateKey, PromisedDateKey, DeliveryDateKey,
            SupplierKey, StoreKey, ProductKey, QuantityOrdered, QuantityReceived,
            LeadTimeDays, DaysDelayed, OnTimeDeliveryFlag, FullOrderFillFlag, ETLRunID
        )
        SELECT
            ShipmentID, PurchaseOrderID, OrderDateKey, PromisedDateKey, DeliveryDateKey,
            SupplierKey, StoreKey, ProductKey, QuantityOrdered, QuantityReceived,
            LeadTimeDays, DaysDelayed, OnTimeDeliveryFlag, FullOrderFillFlag, @ETLRunID
        FROM StagedShipments;

        SET @InsertedCount = @@ROWCOUNT;

        COMMIT TRANSACTION;
        PRINT 'dw.FactShipment loaded: ' + CAST(@InsertedCount AS VARCHAR(20)) + ' records.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

PRINT 'ETL stored procedures created successfully.';
GO
