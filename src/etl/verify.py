"""Read-only warehouse assertions; failures result in a nonzero CLI exit."""
import json
from pathlib import Path
from src.db.connection import db_manager
from src.utils.config import PROJECT_ROOT

CHECKS = {
 'sales_duplicate_grain': 'SELECT COUNT(*) FROM (SELECT TransactionID,TransactionLineID FROM dw.FactSales GROUP BY TransactionID,TransactionLineID HAVING COUNT(*)>1) x',
 'shipment_duplicate_grain': 'SELECT COUNT(*) FROM (SELECT ShipmentID FROM dw.FactShipment GROUP BY ShipmentID HAVING COUNT(*)>1) x',
 'inventory_duplicate_grain': 'SELECT COUNT(*) FROM (SELECT DateKey,ProductKey,StoreKey FROM dw.FactInventorySnapshot GROUP BY DateKey,ProductKey,StoreKey HAVING COUNT(*)>1) x',
 'sales_orphans': '''SELECT COUNT(*) FROM dw.FactSales f LEFT JOIN dw.DimDate d ON d.DateKey=f.DateKey
     LEFT JOIN dw.DimProduct p ON p.ProductKey=f.ProductKey LEFT JOIN dw.DimStore s ON s.StoreKey=f.StoreKey
     LEFT JOIN dw.DimChannel c ON c.ChannelKey=f.ChannelKey LEFT JOIN dw.DimPromotion m ON m.PromotionKey=f.PromotionKey
     LEFT JOIN dw.DimCustomer u ON u.CustomerKey=f.CustomerKey
     WHERE d.DateKey IS NULL OR p.ProductKey IS NULL OR s.StoreKey IS NULL OR c.ChannelKey IS NULL OR m.PromotionKey IS NULL OR (f.CustomerKey IS NOT NULL AND u.CustomerKey IS NULL)''',
 'sales_formula_errors': '''SELECT COUNT(*) FROM dw.FactSales WHERE ABS(GrossSalesAmount-QuantitySold*UnitPrice)>0.0001
     OR ABS(NetSalesAmount-GrossSalesAmount+DiscountAmount)>0.0001 OR ABS(ProfitAmount-NetSalesAmount+CostAmount)>0.0001''',
 'product_multiple_current': 'SELECT COUNT(*) FROM (SELECT SourceProductID FROM dw.DimProduct WHERE IsCurrent=1 GROUP BY SourceProductID HAVING COUNT(*)>1) x',
 'product_temporal_join_errors': '''SELECT COUNT(*) FROM dw.FactSales f JOIN dw.DimProduct p ON p.ProductKey=f.ProductKey JOIN dw.DimDate d ON d.DateKey=f.DateKey
     WHERE d.FullDate<p.EffectiveFrom OR (p.EffectiveTo IS NOT NULL AND d.FullDate>=p.EffectiveTo)''',
 'product_overlapping_intervals': '''SELECT COUNT(*) FROM dw.DimProduct a JOIN dw.DimProduct b ON a.SourceProductID=b.SourceProductID AND a.ProductKey<b.ProductKey
     WHERE a.EffectiveFrom<COALESCE(b.EffectiveTo,'9999-12-31') AND b.EffectiveFrom<COALESCE(a.EffectiveTo,'9999-12-31')''',
 'date_gaps': 'SELECT COALESCE(DATEDIFF(DAY,MIN(FullDate),MAX(FullDate))+1-COUNT(*),0) FROM dw.DimDate',
 'negative_inventory': 'SELECT COUNT(*) FROM dw.FactInventorySnapshot WHERE QuantityOnHand<0 OR QuantityOnOrder<0 OR UnitCost<0',
 'disabled_or_untrusted_constraints': '''SELECT (SELECT COUNT(*) FROM sys.foreign_keys WHERE is_disabled=1 OR is_not_trusted=1) +
     (SELECT COUNT(*) FROM sys.check_constraints WHERE is_disabled=1 OR is_not_trusted=1)''',
 'incorrect_synthetic_tag': "SELECT COUNT(*) FROM dw.FactSales WHERE SourceSystem <> 'SYNTHETIC_CANONICAL'",
 'raw_sales_count_mismatch': 'SELECT ABS((SELECT COUNT(*) FROM raw.SourceSalesTransactionLine)-(SELECT COUNT(*) FROM dw.FactSales))',
 'raw_sales_total_mismatch': '''SELECT ABS(COALESCE((SELECT SUM(LineTotalAmount) FROM raw.SourceSalesTransactionLine),0)-
     COALESCE((SELECT SUM(NetSalesAmount) FROM dw.FactSales),0))''',
 'incomplete_audit_runs': "SELECT COUNT(*) FROM audit.ETLRunHistory WHERE Status='RUNNING'",
}


def verify(manager=None):
    manager = manager or db_manager
    checks = {}
    conn = manager.get_raw_connection()
    cur = conn.cursor()
    try:
        for name, sql in CHECKS.items():
            cur.execute(sql)
            value = cur.fetchone()[0]
            checks[name] = {'value': str(value), 'passed': value == 0}
        rows = {}
        for name in ['DimDate','DimProduct','DimStore','DimCustomer','DimChannel','DimPromotion','DimSupplier','FactSales','FactInventorySnapshot','FactShipment']:
            cur.execute(f'SELECT COUNT(*) AS n FROM dw.{name}')
            rows[name] = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) AS n FROM sys.views WHERE schema_id IN (SCHEMA_ID(\'dw\'),SCHEMA_ID(\'mart\'))')
        view_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) AS n FROM sys.procedures WHERE schema_id IN (SCHEMA_ID(\'dw\'),SCHEMA_ID(\'audit\'))')
        procedure_count = cur.fetchone()[0]
        for path in ['09_olap_examples.sql','10_data_quality_checks.sql','12_reporting_queries.sql']:
            from src.db.executor import split_batches
            from src.utils.config import PROJECT_ROOT
            for batch in split_batches((PROJECT_ROOT/'sql'/path).read_text()):
                cur.execute(batch)
                while cur.nextset():
                    pass
            checks[path] = {'passed': True, 'value': 'Executed against SQL Server'}
    finally:
        cur.close()
        conn.close()
    report = {'passed': all(c['passed'] for c in checks.values()) and rows['FactSales']>0,
              'checks': checks, 'warehouse_rows': rows, 'reporting_views': view_count,
              'etl_procedures': procedure_count}
    out = PROJECT_ROOT / 'reports/generated'; out.mkdir(parents=True,exist_ok=True)
    (out/'warehouse_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
