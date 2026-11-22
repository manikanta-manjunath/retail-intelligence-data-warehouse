from decimal import Decimal

import pytest

from src.db.connection import db_manager


@pytest.mark.integration
def test_loaded_warehouse_and_repeatable_second_run():
    with db_manager.session_scope() as cursor:
        cursor.execute(
            """SELECT TOP 2 ETLRunID,Status,SourceRowCount,InsertedRowCount,
                      UpdatedRowCount,RejectedRowCount
               FROM audit.ETLRunHistory
               WHERE Status='SUCCESS' AND SourceRowCount=242809
               ORDER BY ETLRunID DESC"""
        )
        runs = cursor.fetchall()
        assert [row["Status"] for row in runs] == ["SUCCESS", "SUCCESS"]
        assert runs[0]["InsertedRowCount"] == 0
        assert runs[0]["UpdatedRowCount"] == 0
        assert runs[0]["RejectedRowCount"] == 0
        assert runs[1]["InsertedRowCount"] == 173057
        cursor.execute(
            """SELECT COUNT(*) AS Lines,SUM(NetSalesAmount) AS NetSales,
                      COUNT(DISTINCT TransactionID) AS Transactions
               FROM dw.FactSales"""
        )
        facts = cursor.fetchone()
        assert facts["Lines"] == 182176
        assert facts["Transactions"] == 73213
        assert facts["NetSales"] == Decimal("16976377.1400")
        cursor.execute(
            """SELECT MIN(d.FullDate) AS StartDate,MAX(d.FullDate) AS EndDate,
                      COUNT(DISTINCT d.YearNumber) AS Years
               FROM dw.FactSales f JOIN dw.DimDate d ON d.DateKey=f.DateKey"""
        )
        coverage = cursor.fetchone()
        assert str(coverage['StartDate']) == '2010-01-01'
        assert str(coverage['EndDate']) == '2024-12-31'
        assert coverage['Years'] == 15
        cursor.execute('SELECT COUNT(*) AS Labels FROM audit.SyntheticAnomalyGroundTruth')
        assert cursor.fetchone()['Labels'] == 1607


@pytest.mark.integration
def test_product_scd2_change_is_historical_and_rolled_back():
    conn = db_manager.get_raw_connection()
    cursor = conn.cursor(as_dict=True)
    try:
        cursor.execute(
            """SELECT COUNT(*) AS Versions,MAX(BasePrice) AS Price
               FROM dw.DimProduct WHERE SourceProductID='PROD-001'"""
        )
        before = cursor.fetchone()
        cursor.execute(
            """INSERT INTO audit.ETLRunHistory
               (PipelineName,ExecutionMode,StartTime,Status)
               VALUES ('SCD_ROLLBACK_TEST','TEST',SYSUTCDATETIME(),'RUNNING');
               SELECT SCOPE_IDENTITY() AS ETLRunID"""
        )
        run_id = int(cursor.fetchone()["ETLRunID"])
        cursor.execute(
            """INSERT INTO stg.SourceProduct
               (SourceProductID,ProductName,Category,Subcategory,Brand,UnitCost,
                BasePrice,UnitOfMeasure,SourceSupplierID,CreatedDate,ModifiedDate,ETLRunID)
               SELECT SourceProductID,ProductName,Category,Subcategory,Brand,UnitCost,
                      BasePrice+1.0000,UnitOfMeasure,SourceSupplierID,CreatedDate,
                      DATEADD(SECOND,1,SYSUTCDATETIME()),%s
               FROM raw.SourceProduct WHERE SourceProductID='PROD-001'""",
            (run_id,),
        )
        cursor.execute("EXEC dw.usp_LoadDimProduct_SCD2 @ETLRunID=%s", (run_id,))
        while cursor.nextset():
            pass
        cursor.execute(
            """SELECT COUNT(*) AS Versions,SUM(CASE WHEN IsCurrent=1 THEN 1 ELSE 0 END) AS CurrentRows,
                      MAX(VersionNumber) AS LatestVersion
               FROM dw.DimProduct WHERE SourceProductID='PROD-001'"""
        )
        changed = cursor.fetchone()
        assert changed["Versions"] == before["Versions"] + 1
        assert changed["CurrentRows"] == 1
        assert changed["LatestVersion"] == 2
    finally:
        conn.rollback()
        cursor.close()
        conn.close()
    with db_manager.session_scope() as cursor:
        cursor.execute(
            """SELECT COUNT(*) AS Versions,MAX(BasePrice) AS Price
               FROM dw.DimProduct WHERE SourceProductID='PROD-001'"""
        )
        after = cursor.fetchone()
    assert after == before
