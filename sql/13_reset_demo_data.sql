-- ============================================================================
-- Script: 13_reset_demo_data.sql
-- Description: Safely truncates warehouse facts and raw staging tables
--              for clean classroom demo reruns without dropping table schemas.
-- ============================================================================

USE [RetailIntelligenceDW];
GO

PRINT 'WARNING: Resetting demo data in RetailIntelligenceDW...';

-- Disable Foreign Key Constraints temporarily
ALTER TABLE dw.FactSales NOCHECK CONSTRAINT ALL;
ALTER TABLE dw.FactInventorySnapshot NOCHECK CONSTRAINT ALL;
ALTER TABLE dw.FactShipment NOCHECK CONSTRAINT ALL;
GO

-- Truncate Fact Tables
TRUNCATE TABLE dw.FactSales;
TRUNCATE TABLE dw.FactInventorySnapshot;
TRUNCATE TABLE dw.FactShipment;
GO

-- Re-enable Foreign Key Constraints
ALTER TABLE dw.FactSales CHECK CONSTRAINT ALL;
ALTER TABLE dw.FactInventorySnapshot CHECK CONSTRAINT ALL;
ALTER TABLE dw.FactShipment CHECK CONSTRAINT ALL;
GO

-- Clear Raw Source Tables
TRUNCATE TABLE raw.SourceSalesTransactionLine;
TRUNCATE TABLE raw.SourceSalesTransaction;
TRUNCATE TABLE raw.SourceInventory;
TRUNCATE TABLE raw.SourceShipment;
GO

PRINT 'Demo data reset completed successfully.';
GO
