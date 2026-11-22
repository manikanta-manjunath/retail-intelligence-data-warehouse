-- ============================================================================
-- Script: 05_create_constraints_indexes.sql
-- Description: Applies foreign key constraints, unique business constraints,
--              and performance indexes on the dimensional star schema.
-- ============================================================================

USE [RetailIntelligenceDW];
GO

-- ----------------------------------------------------------------------------
-- 1. Foreign Key Constraints for FactSales
-- ----------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_FactSales_DimDate')
BEGIN
    ALTER TABLE dw.FactSales
    ADD CONSTRAINT FK_FactSales_DimDate
    FOREIGN KEY (DateKey) REFERENCES dw.DimDate(DateKey);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_FactSales_DimProduct')
BEGIN
    ALTER TABLE dw.FactSales
    ADD CONSTRAINT FK_FactSales_DimProduct
    FOREIGN KEY (ProductKey) REFERENCES dw.DimProduct(ProductKey);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_FactSales_DimStore')
BEGIN
    ALTER TABLE dw.FactSales
    ADD CONSTRAINT FK_FactSales_DimStore
    FOREIGN KEY (StoreKey) REFERENCES dw.DimStore(StoreKey);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_FactSales_DimChannel')
BEGIN
    ALTER TABLE dw.FactSales
    ADD CONSTRAINT FK_FactSales_DimChannel
    FOREIGN KEY (ChannelKey) REFERENCES dw.DimChannel(ChannelKey);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_FactSales_DimPromotion')
BEGIN
    ALTER TABLE dw.FactSales
    ADD CONSTRAINT FK_FactSales_DimPromotion
    FOREIGN KEY (PromotionKey) REFERENCES dw.DimPromotion(PromotionKey);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_FactSales_DimCustomer')
BEGIN
    ALTER TABLE dw.FactSales
    ADD CONSTRAINT FK_FactSales_DimCustomer
    FOREIGN KEY (CustomerKey) REFERENCES dw.DimCustomer(CustomerKey);
END;
GO

-- ----------------------------------------------------------------------------
-- 2. Foreign Key Constraints for FactInventorySnapshot
-- ----------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_FactInventorySnapshot_DimDate')
BEGIN
    ALTER TABLE dw.FactInventorySnapshot
    ADD CONSTRAINT FK_FactInventorySnapshot_DimDate
    FOREIGN KEY (DateKey) REFERENCES dw.DimDate(DateKey);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_FactInventorySnapshot_DimProduct')
BEGIN
    ALTER TABLE dw.FactInventorySnapshot
    ADD CONSTRAINT FK_FactInventorySnapshot_DimProduct
    FOREIGN KEY (ProductKey) REFERENCES dw.DimProduct(ProductKey);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_FactInventorySnapshot_DimStore')
BEGIN
    ALTER TABLE dw.FactInventorySnapshot
    ADD CONSTRAINT FK_FactInventorySnapshot_DimStore
    FOREIGN KEY (StoreKey) REFERENCES dw.DimStore(StoreKey);
END;
GO

-- ----------------------------------------------------------------------------
-- 3. Foreign Key Constraints for FactShipment
-- ----------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_FactShipment_Supplier')
BEGIN
    ALTER TABLE dw.FactShipment
    ADD CONSTRAINT FK_FactShipment_Supplier
    FOREIGN KEY (SupplierKey) REFERENCES dw.DimSupplier(SupplierKey);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_FactShipment_Store')
BEGIN
    ALTER TABLE dw.FactShipment
    ADD CONSTRAINT FK_FactShipment_Store
    FOREIGN KEY (StoreKey) REFERENCES dw.DimStore(StoreKey);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_FactShipment_Product')
BEGIN
    ALTER TABLE dw.FactShipment
    ADD CONSTRAINT FK_FactShipment_Product
    FOREIGN KEY (ProductKey) REFERENCES dw.DimProduct(ProductKey);
END;
GO

-- ----------------------------------------------------------------------------
-- 4. Unique Constraints to Guard Grain and Prevent Duplicate Reloads
-- ----------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_FactSales_TransactionLine' AND object_id = OBJECT_ID('dw.FactSales'))
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UQ_FactSales_TransactionLine
    ON dw.FactSales (TransactionID, TransactionLineID);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_FactInventorySnapshot_Grain' AND object_id = OBJECT_ID('dw.FactInventorySnapshot'))
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UQ_FactInventorySnapshot_Grain
    ON dw.FactInventorySnapshot (DateKey, ProductKey, StoreKey);
END;
GO

-- ----------------------------------------------------------------------------
-- 5. Performance Indexes on Star Schema Joins and Common Analytical Filters
-- ----------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FactSales_DateKey' AND object_id = OBJECT_ID('dw.FactSales'))
    CREATE NONCLUSTERED INDEX IX_FactSales_DateKey ON dw.FactSales (DateKey) INCLUDE (NetSalesAmount, QuantitySold);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FactSales_ProductKey' AND object_id = OBJECT_ID('dw.FactSales'))
    CREATE NONCLUSTERED INDEX IX_FactSales_ProductKey ON dw.FactSales (ProductKey) INCLUDE (NetSalesAmount, QuantitySold);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FactSales_StoreKey' AND object_id = OBJECT_ID('dw.FactSales'))
    CREATE NONCLUSTERED INDEX IX_FactSales_StoreKey ON dw.FactSales (StoreKey) INCLUDE (NetSalesAmount, QuantitySold);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FactSales_CustomerKey' AND object_id = OBJECT_ID('dw.FactSales'))
    CREATE NONCLUSTERED INDEX IX_FactSales_CustomerKey ON dw.FactSales (CustomerKey) INCLUDE (NetSalesAmount, DateKey);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FactInventory_DateProduct' AND object_id = OBJECT_ID('dw.FactInventorySnapshot'))
    CREATE NONCLUSTERED INDEX IX_FactInventory_DateProduct ON dw.FactInventorySnapshot (DateKey, ProductKey) INCLUDE (QuantityOnHand, ReorderPoint);
GO

PRINT 'Foreign keys, uniqueness guards, and performance indexes created successfully.';
GO
