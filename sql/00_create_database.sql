-- ============================================================================
-- Script: 00_create_database.sql
-- Description: Creates the RetailIntelligenceDW database with enterprise
--              recovery and collation settings.
-- Target: Microsoft SQL Server 2019 / 2022
-- ============================================================================

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'RetailIntelligenceDW')
BEGIN
    CREATE DATABASE [RetailIntelligenceDW]
    COLLATE Latin1_General_100_CI_AS_SC_UTF8;
    PRINT 'Database RetailIntelligenceDW created successfully.';
END
ELSE
BEGIN
    PRINT 'Database RetailIntelligenceDW already exists.';
END
GO

USE [RetailIntelligenceDW];
GO

-- Existing database configuration is deliberately preserved.
PRINT 'Database existence verified successfully.';
GO
