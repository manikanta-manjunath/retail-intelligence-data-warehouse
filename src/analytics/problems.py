"""Detect auditable business and data-quality problems from warehouse facts."""
import numpy as np
import pandas as pd

from src.analytics.data import query


COLUMNS = [
    'ProblemDate', 'ProblemType', 'Severity', 'EntityType', 'EntityID',
    'MetricValue', 'Threshold', 'Description',
]


def _row(date, problem, severity, entity_type, entity_id, value, threshold, description):
    return {
        'ProblemDate': str(pd.Timestamp(date).date()) if pd.notna(date) else None,
        'ProblemType': problem,
        'Severity': severity,
        'EntityType': entity_type,
        'EntityID': str(entity_id),
        'MetricValue': None if pd.isna(value) else float(value),
        'Threshold': threshold,
        'Description': description,
    }


def detect_problems(sales):
    rows = []
    frame = sales.copy()
    frame['FullDate'] = pd.to_datetime(frame.FullDate)

    daily = frame.groupby('FullDate').NetSalesAmount.sum().sort_index()
    baseline = daily.rolling(28, center=True, min_periods=14).median()
    deviation = (daily - baseline).abs()
    mad = deviation.rolling(28, center=True, min_periods=14).median().replace(0, np.nan)
    robust_z = 0.6745 * (daily - baseline) / mad
    for stamp, score in robust_z[robust_z.abs() >= 4].items():
        direction = 'SPIKE' if score > 0 else 'DROP'
        rows.append(_row(stamp, f'SALES_{direction}', 'HIGH', 'ALL_SALES', 'ALL',
                         score, '|robust z| >= 4',
                         f'Daily sales {direction.lower()} versus the centered 28-day median.'))

    annual = frame.groupby(frame.FullDate.dt.year).NetSalesAmount.sum().sort_index()
    yoy = annual.pct_change() * 100
    for year, change in yoy[yoy < -5].items():
        rows.append(_row(f'{int(year)}-12-31', 'YEAR_OVER_YEAR_DECLINE', 'HIGH',
                         'YEAR', year, change, 'YoY < -5%',
                         'Annual net sales declined by more than 5% versus the prior year.'))

    monthly_margin = frame.assign(Month=frame.FullDate.dt.to_period('M').dt.to_timestamp()).groupby(
        ['Month', 'Category'], as_index=False
    ).agg(NetSales=('NetSalesAmount','sum'), Profit=('ProfitAmount','sum'))
    monthly_margin['MarginPercent'] = np.where(
        monthly_margin.NetSales != 0,
        monthly_margin.Profit / monthly_margin.NetSales * 100,
        np.nan,
    )
    for item in monthly_margin[monthly_margin.MarginPercent < 5].itertuples():
        severity = 'CRITICAL' if item.MarginPercent < 0 else 'HIGH'
        rows.append(_row(item.Month, 'LOW_OR_NEGATIVE_MARGIN', severity, 'CATEGORY',
                         item.Category, item.MarginPercent, 'Margin < 5%',
                         'Monthly category gross margin is below the review threshold.'))

    discount_rate = np.where(
        frame.GrossSalesAmount.astype(float) > 0,
        frame.DiscountAmount.astype(float) / frame.GrossSalesAmount.astype(float) * 100,
        0,
    )
    discounted = frame.loc[discount_rate > 20, ['FullDate','TransactionID']].copy()
    discounted['DiscountPercent'] = discount_rate[discount_rate > 20]
    for item in discounted.itertuples():
        rows.append(_row(item.FullDate, 'EXCESSIVE_DISCOUNT', 'MEDIUM', 'TRANSACTION',
                         item.TransactionID, item.DiscountPercent, 'Discount > 20%',
                         'A sales line exceeded the configured discount review threshold.'))

    observed = pd.DatetimeIndex(frame.FullDate.dt.normalize().unique())
    expected = pd.date_range(frame.FullDate.min().normalize(), frame.FullDate.max().normalize())
    for stamp in expected.difference(observed):
        rows.append(_row(stamp, 'MISSING_SALES_DATE', 'MEDIUM', 'DATE', stamp.date(),
                         0, 'No sales lines', 'No sales transactions were recorded on this date.'))

    inventory = query('''SELECT SnapshotDate,SourceStoreID,Category,
        SUM(CAST(StockoutFlag AS INT)) AS Stockouts,
        SUM(CAST(UnderStockFlag AS INT)) AS Understock
        FROM dw.vw_InventoryPosition
        WHERE StockoutFlag=1 OR UnderStockFlag=1
        GROUP BY SnapshotDate,SourceStoreID,Category''')
    for item in inventory.itertuples():
        if item.Stockouts:
            rows.append(_row(item.SnapshotDate, 'STOCKOUT', 'CRITICAL', 'STORE_CATEGORY',
                             f'{item.SourceStoreID}/{item.Category}', item.Stockouts,
                             'Stockout count > 0', 'One or more tracked SKUs were out of stock.'))
        elif item.Understock:
            rows.append(_row(item.SnapshotDate, 'UNDERSTOCK', 'HIGH', 'STORE_CATEGORY',
                             f'{item.SourceStoreID}/{item.Category}', item.Understock,
                             'Understock count > 0', 'One or more tracked SKUs were below reorder point.'))

    shipments = query('''SELECT d.FullDate,s.SourceSupplierID,
        SUM(CASE WHEN f.DaysDelayed>0 THEN 1 ELSE 0 END) AS Delayed,
        SUM(CASE WHEN f.FullOrderFillFlag=0 THEN 1 ELSE 0 END) AS Partial
        FROM dw.FactShipment f JOIN dw.DimDate d ON d.DateKey=f.DeliveryDateKey
        JOIN dw.DimSupplier s ON s.SupplierKey=f.SupplierKey
        WHERE f.DaysDelayed>0 OR f.FullOrderFillFlag=0
        GROUP BY d.FullDate,s.SourceSupplierID''')
    for item in shipments.itertuples():
        if item.Delayed:
            rows.append(_row(item.FullDate, 'SUPPLIER_DELAY', 'HIGH', 'SUPPLIER',
                             item.SourceSupplierID, item.Delayed, 'Delayed shipments > 0',
                             'Supplier deliveries arrived after the promised date.'))
        if item.Partial:
            rows.append(_row(item.FullDate, 'PARTIAL_FILL', 'MEDIUM', 'SUPPLIER',
                             item.SourceSupplierID, item.Partial, 'Partial fills > 0',
                             'Supplier deliveries did not completely fill ordered quantity.'))

    quality = query('''SELECT q.CheckTimestamp,q.TableName,q.CheckType,q.RecordsFailed,q.Severity,q.Status
        FROM audit.DataQualityLog q WHERE q.Status<>'PASSED' OR q.RecordsFailed>0''')
    for item in quality.itertuples():
        rows.append(_row(item.CheckTimestamp, 'DATA_QUALITY_FAILURE',
                         str(item.Severity).upper(), 'TABLE', item.TableName,
                         item.RecordsFailed, 'Status must be PASSED',
                         f'{item.CheckType} check reported {item.Status}.'))

    return pd.DataFrame(rows, columns=COLUMNS).sort_values(
        ['ProblemDate','Severity','ProblemType'], ascending=[False, True, True]
    ).reset_index(drop=True)
