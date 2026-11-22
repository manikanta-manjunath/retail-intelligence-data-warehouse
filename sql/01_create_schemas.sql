-- ============================================================================
-- Script: 01_create_schemas.sql
-- Description: Creates the 5 functional warehouse schemas:
--              1. raw   - Ingested raw source data and batch staging
--              2. stg   - Cleaned, validated, standardized staging tables
--              3. dw    - Conformed dimensions and fact star-schema tables
--              4. mart  - Analytical views, data marts, reporting objects
--              5. audit - Pipeline logging, data quality metrics, run history
-- ============================================================================

USE [RetailIntelligenceDW];
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'raw')
    EXEC('CREATE SCHEMA [raw];');
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'stg')
    EXEC('CREATE SCHEMA [stg];');
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'dw')
    EXEC('CREATE SCHEMA [dw];');
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'mart')
    EXEC('CREATE SCHEMA [mart];');
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'audit')
    EXEC('CREATE SCHEMA [audit];');
GO

PRINT 'Schemas raw, stg, dw, mart, audit created/verified successfully.';
GO
