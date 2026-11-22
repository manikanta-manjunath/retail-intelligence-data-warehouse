-- Non-destructive ETL reliability migration. Fails if existing data violates grain.
USE [RetailIntelligenceDW];
GO
DECLARE @SourceSystemDefault SYSNAME;
SELECT @SourceSystemDefault = dc.name
FROM sys.default_constraints dc
JOIN sys.columns c ON c.default_object_id = dc.object_id
WHERE dc.parent_object_id = OBJECT_ID('dw.FactSales')
  AND c.name = 'SourceSystem';
IF @SourceSystemDefault IS NOT NULL
    EXEC('ALTER TABLE dw.FactSales DROP CONSTRAINT [' + @SourceSystemDefault + ']');
ALTER TABLE dw.FactSales ADD CONSTRAINT DF_FactSales_SourceSystem
    DEFAULT 'UNDECLARED' FOR SourceSystem;
GO
IF OBJECT_ID('raw.IngestedRecord','U') IS NULL
CREATE TABLE raw.IngestedRecord (
    ETLRunID INT NOT NULL REFERENCES audit.ETLRunHistory(ETLRunID),
    EntityName NVARCHAR(100) NOT NULL, SourceRowNumber INT NOT NULL,
    SourceSystem NVARCHAR(50) NOT NULL, RecordHash CHAR(64) NOT NULL,
    Payload NVARCHAR(MAX) NOT NULL CHECK (ISJSON(Payload)=1),
    IngestedAt DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
    PRIMARY KEY (ETLRunID,EntityName,SourceRowNumber)
);
GO
IF OBJECT_ID('audit.RejectedRecord','U') IS NULL
CREATE TABLE audit.RejectedRecord (
    ETLRunID INT NOT NULL REFERENCES audit.ETLRunHistory(ETLRunID),
    EntityName NVARCHAR(100) NOT NULL, SourceRowNumber INT NOT NULL,
    Reason NVARCHAR(1000) NOT NULL, Payload NVARCHAR(MAX) NOT NULL,
    PRIMARY KEY (ETLRunID,EntityName,SourceRowNumber)
);
GO
IF OBJECT_ID('audit.IngestionManifest','U') IS NULL
CREATE TABLE audit.IngestionManifest (
    ETLRunID INT PRIMARY KEY REFERENCES audit.ETLRunHistory(ETLRunID),
    SourceSystem NVARCHAR(50) NOT NULL, ManifestJSON NVARCHAR(MAX) NOT NULL CHECK (ISJSON(ManifestJSON)=1)
);
GO
IF OBJECT_ID('audit.SyntheticAnomalyGroundTruth','U') IS NULL
CREATE TABLE audit.SyntheticAnomalyGroundTruth (
    SourceSystem NVARCHAR(50) NOT NULL,
    TransactionID NVARCHAR(50) NOT NULL,
    TransactionLineID INT NOT NULL,
    AnomalyType NVARCHAR(100) NOT NULL,
    FirstSeenETLRunID INT NOT NULL REFERENCES audit.ETLRunHistory(ETLRunID),
    CreatedAt DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_SyntheticAnomalyGroundTruth
        PRIMARY KEY (SourceSystem, TransactionID, TransactionLineID, AnomalyType)
);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('raw.SourceCalendar') AND name='UQ_SourceCalendar_BusinessKey')
    CREATE UNIQUE INDEX UQ_SourceCalendar_BusinessKey ON raw.SourceCalendar ([CalendarDate]);
GO
IF OBJECT_ID('stg.SourceCalendar','U') IS NULL
BEGIN
    SELECT TOP (0) * INTO stg.SourceCalendar FROM raw.SourceCalendar;
    ALTER TABLE stg.SourceCalendar ADD ETLRunID INT NOT NULL;
    ALTER TABLE stg.SourceCalendar ADD CONSTRAINT FK_Stg_SourceCalendar_Run FOREIGN KEY (ETLRunID) REFERENCES audit.ETLRunHistory(ETLRunID);
    CREATE UNIQUE INDEX UQ_Stg_SourceCalendar ON stg.SourceCalendar (ETLRunID, [CalendarDate]);
END;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('raw.SourceSupplier') AND name='UQ_SourceSupplier_BusinessKey')
    CREATE UNIQUE INDEX UQ_SourceSupplier_BusinessKey ON raw.SourceSupplier ([SourceSupplierID]);
GO
IF OBJECT_ID('stg.SourceSupplier','U') IS NULL
BEGIN
    SELECT TOP (0) * INTO stg.SourceSupplier FROM raw.SourceSupplier;
    ALTER TABLE stg.SourceSupplier ADD ETLRunID INT NOT NULL;
    ALTER TABLE stg.SourceSupplier ADD CONSTRAINT FK_Stg_SourceSupplier_Run FOREIGN KEY (ETLRunID) REFERENCES audit.ETLRunHistory(ETLRunID);
    CREATE UNIQUE INDEX UQ_Stg_SourceSupplier ON stg.SourceSupplier (ETLRunID, [SourceSupplierID]);
END;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('raw.SourceProduct') AND name='UQ_SourceProduct_BusinessKey')
    CREATE UNIQUE INDEX UQ_SourceProduct_BusinessKey ON raw.SourceProduct ([SourceProductID]);
GO
IF OBJECT_ID('stg.SourceProduct','U') IS NULL
BEGIN
    SELECT TOP (0) * INTO stg.SourceProduct FROM raw.SourceProduct;
    ALTER TABLE stg.SourceProduct ADD ETLRunID INT NOT NULL;
    ALTER TABLE stg.SourceProduct ADD CONSTRAINT FK_Stg_SourceProduct_Run FOREIGN KEY (ETLRunID) REFERENCES audit.ETLRunHistory(ETLRunID);
    CREATE UNIQUE INDEX UQ_Stg_SourceProduct ON stg.SourceProduct (ETLRunID, [SourceProductID]);
END;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('raw.SourceStore') AND name='UQ_SourceStore_BusinessKey')
    CREATE UNIQUE INDEX UQ_SourceStore_BusinessKey ON raw.SourceStore ([SourceStoreID]);
GO
IF OBJECT_ID('stg.SourceStore','U') IS NULL
BEGIN
    SELECT TOP (0) * INTO stg.SourceStore FROM raw.SourceStore;
    ALTER TABLE stg.SourceStore ADD ETLRunID INT NOT NULL;
    ALTER TABLE stg.SourceStore ADD CONSTRAINT FK_Stg_SourceStore_Run FOREIGN KEY (ETLRunID) REFERENCES audit.ETLRunHistory(ETLRunID);
    CREATE UNIQUE INDEX UQ_Stg_SourceStore ON stg.SourceStore (ETLRunID, [SourceStoreID]);
END;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('raw.SourceCustomer') AND name='UQ_SourceCustomer_BusinessKey')
    CREATE UNIQUE INDEX UQ_SourceCustomer_BusinessKey ON raw.SourceCustomer ([SourceCustomerID]);
GO
IF OBJECT_ID('stg.SourceCustomer','U') IS NULL
BEGIN
    SELECT TOP (0) * INTO stg.SourceCustomer FROM raw.SourceCustomer;
    ALTER TABLE stg.SourceCustomer ADD ETLRunID INT NOT NULL;
    ALTER TABLE stg.SourceCustomer ADD CONSTRAINT FK_Stg_SourceCustomer_Run FOREIGN KEY (ETLRunID) REFERENCES audit.ETLRunHistory(ETLRunID);
    CREATE UNIQUE INDEX UQ_Stg_SourceCustomer ON stg.SourceCustomer (ETLRunID, [SourceCustomerID]);
END;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('raw.SourcePromotion') AND name='UQ_SourcePromotion_BusinessKey')
    CREATE UNIQUE INDEX UQ_SourcePromotion_BusinessKey ON raw.SourcePromotion ([PromotionID]);
GO
IF OBJECT_ID('stg.SourcePromotion','U') IS NULL
BEGIN
    SELECT TOP (0) * INTO stg.SourcePromotion FROM raw.SourcePromotion;
    ALTER TABLE stg.SourcePromotion ADD ETLRunID INT NOT NULL;
    ALTER TABLE stg.SourcePromotion ADD CONSTRAINT FK_Stg_SourcePromotion_Run FOREIGN KEY (ETLRunID) REFERENCES audit.ETLRunHistory(ETLRunID);
    CREATE UNIQUE INDEX UQ_Stg_SourcePromotion ON stg.SourcePromotion (ETLRunID, [PromotionID]);
END;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('raw.SourceSalesTransaction') AND name='UQ_SourceSalesTransaction_BusinessKey')
    CREATE UNIQUE INDEX UQ_SourceSalesTransaction_BusinessKey ON raw.SourceSalesTransaction ([TransactionID]);
GO
IF OBJECT_ID('stg.SourceSalesTransaction','U') IS NULL
BEGIN
    SELECT TOP (0) * INTO stg.SourceSalesTransaction FROM raw.SourceSalesTransaction;
    ALTER TABLE stg.SourceSalesTransaction ADD ETLRunID INT NOT NULL;
    ALTER TABLE stg.SourceSalesTransaction ADD CONSTRAINT FK_Stg_SourceSalesTransaction_Run FOREIGN KEY (ETLRunID) REFERENCES audit.ETLRunHistory(ETLRunID);
    CREATE UNIQUE INDEX UQ_Stg_SourceSalesTransaction ON stg.SourceSalesTransaction (ETLRunID, [TransactionID]);
END;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('raw.SourceSalesTransactionLine') AND name='UQ_SourceSalesTransactionLine_BusinessKey')
    CREATE UNIQUE INDEX UQ_SourceSalesTransactionLine_BusinessKey ON raw.SourceSalesTransactionLine ([TransactionID], [LineNumber]);
GO
IF OBJECT_ID('stg.SourceSalesTransactionLine','U') IS NULL
BEGIN
    SELECT TOP (0) * INTO stg.SourceSalesTransactionLine FROM raw.SourceSalesTransactionLine;
    ALTER TABLE stg.SourceSalesTransactionLine ADD ETLRunID INT NOT NULL;
    ALTER TABLE stg.SourceSalesTransactionLine ADD CONSTRAINT FK_Stg_SourceSalesTransactionLine_Run FOREIGN KEY (ETLRunID) REFERENCES audit.ETLRunHistory(ETLRunID);
    CREATE UNIQUE INDEX UQ_Stg_SourceSalesTransactionLine ON stg.SourceSalesTransactionLine (ETLRunID, [TransactionID], [LineNumber]);
END;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('raw.SourceInventory') AND name='UQ_SourceInventory_BusinessKey')
    CREATE UNIQUE INDEX UQ_SourceInventory_BusinessKey ON raw.SourceInventory ([SnapshotDate], [SourceStoreID], [SourceProductID]);
GO
IF OBJECT_ID('stg.SourceInventory','U') IS NULL
BEGIN
    SELECT TOP (0) * INTO stg.SourceInventory FROM raw.SourceInventory;
    ALTER TABLE stg.SourceInventory ADD ETLRunID INT NOT NULL;
    ALTER TABLE stg.SourceInventory ADD CONSTRAINT FK_Stg_SourceInventory_Run FOREIGN KEY (ETLRunID) REFERENCES audit.ETLRunHistory(ETLRunID);
    CREATE UNIQUE INDEX UQ_Stg_SourceInventory ON stg.SourceInventory (ETLRunID, [SnapshotDate], [SourceStoreID], [SourceProductID]);
END;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('raw.SourceShipment') AND name='UQ_SourceShipment_BusinessKey')
    CREATE UNIQUE INDEX UQ_SourceShipment_BusinessKey ON raw.SourceShipment ([ShipmentID]);
GO
IF OBJECT_ID('stg.SourceShipment','U') IS NULL
BEGIN
    SELECT TOP (0) * INTO stg.SourceShipment FROM raw.SourceShipment;
    ALTER TABLE stg.SourceShipment ADD ETLRunID INT NOT NULL;
    ALTER TABLE stg.SourceShipment ADD CONSTRAINT FK_Stg_SourceShipment_Run FOREIGN KEY (ETLRunID) REFERENCES audit.ETLRunHistory(ETLRunID);
    CREATE UNIQUE INDEX UQ_Stg_SourceShipment ON stg.SourceShipment (ETLRunID, [ShipmentID]);
END;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dw.DimProduct') AND name='UQ_DimProduct_BusinessKey')
CREATE UNIQUE INDEX UQ_DimProduct_BusinessKey ON dw.DimProduct (SourceProductID) WHERE IsCurrent = 1;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dw.DimStore') AND name='UQ_DimStore_BusinessKey')
CREATE UNIQUE INDEX UQ_DimStore_BusinessKey ON dw.DimStore (SourceStoreID) WHERE IsCurrent = 1;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dw.DimCustomer') AND name='UQ_DimCustomer_BusinessKey')
CREATE UNIQUE INDEX UQ_DimCustomer_BusinessKey ON dw.DimCustomer (SourceCustomerID) WHERE IsCurrent = 1;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dw.DimSupplier') AND name='UQ_DimSupplier_BusinessKey')
CREATE UNIQUE INDEX UQ_DimSupplier_BusinessKey ON dw.DimSupplier (SourceSupplierID);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dw.DimPromotion') AND name='UQ_DimPromotion_BusinessKey')
CREATE UNIQUE INDEX UQ_DimPromotion_BusinessKey ON dw.DimPromotion (PromotionID);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dw.FactShipment') AND name='UQ_FactShipment_BusinessKey')
CREATE UNIQUE INDEX UQ_FactShipment_BusinessKey ON dw.FactShipment (ShipmentID);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Shipment_OrderDateKey')
ALTER TABLE dw.FactShipment ADD CONSTRAINT FK_Shipment_OrderDateKey FOREIGN KEY (OrderDateKey) REFERENCES dw.DimDate(DateKey);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Shipment_PromisedDateKey')
ALTER TABLE dw.FactShipment ADD CONSTRAINT FK_Shipment_PromisedDateKey FOREIGN KEY (PromisedDateKey) REFERENCES dw.DimDate(DateKey);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_Shipment_DeliveryDateKey')
ALTER TABLE dw.FactShipment ADD CONSTRAINT FK_Shipment_DeliveryDateKey FOREIGN KEY (DeliveryDateKey) REFERENCES dw.DimDate(DateKey);
GO
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name='CK_FactSales_Measures')
ALTER TABLE dw.FactSales WITH CHECK ADD CONSTRAINT CK_FactSales_Measures CHECK (QuantitySold > 0 AND UnitPrice >= 0 AND DiscountAmount >= 0 AND DiscountAmount <= GrossSalesAmount AND ABS(GrossSalesAmount-QuantitySold*UnitPrice)<0.0002 AND ABS(NetSalesAmount-GrossSalesAmount+DiscountAmount)<0.0002 AND ABS(ProfitAmount-NetSalesAmount+CostAmount)<0.0002);
GO
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name='CK_FactInventorySnapshot_Measures')
ALTER TABLE dw.FactInventorySnapshot WITH CHECK ADD CONSTRAINT CK_FactInventorySnapshot_Measures CHECK (QuantityOnHand>=0 AND QuantityOnOrder>=0 AND ReorderPoint>=0 AND SafetyStock>=0 AND UnitCost>=0);
GO
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name='CK_FactShipment_Measures')
ALTER TABLE dw.FactShipment WITH CHECK ADD CONSTRAINT CK_FactShipment_Measures CHECK (QuantityOrdered>0 AND QuantityReceived>=0 AND LeadTimeDays>=0 AND DaysDelayed>=0);
GO
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name='CK_DimProduct_Measures')
ALTER TABLE dw.DimProduct WITH CHECK ADD CONSTRAINT CK_DimProduct_Measures CHECK (BasePrice>=0 AND UnitCost>=0 AND ((IsCurrent=1 AND EffectiveTo IS NULL) OR (IsCurrent=0 AND EffectiveTo>=EffectiveFrom)));
GO
