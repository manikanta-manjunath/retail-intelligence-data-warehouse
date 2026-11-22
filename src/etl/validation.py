"""Validate canonical records against the preserved SQL source schema."""
from decimal import Decimal, InvalidOperation
from datetime import date, datetime, time
from pathlib import Path
import re
import pandas as pd
from src.utils.config import PROJECT_ROOT

KEYS = {
    'SourceCalendar': ['CalendarDate'], 'SourceSupplier': ['SourceSupplierID'],
    'SourceProduct': ['SourceProductID'], 'SourceStore': ['SourceStoreID'],
    'SourceCustomer': ['SourceCustomerID'], 'SourcePromotion': ['PromotionID'],
    'SourceSalesTransaction': ['TransactionID'],
    'SourceSalesTransactionLine': ['TransactionID', 'LineNumber'],
    'SourceInventory': ['SnapshotDate', 'SourceStoreID', 'SourceProductID'],
    'SourceShipment': ['ShipmentID'],
}


def source_schema():
    """Read column types from this project's source DDL, the ingestion contract."""
    sql = (PROJECT_ROOT / 'sql/02_create_source_tables.sql').read_text()
    schema = {}
    for name, body in re.findall(r'CREATE TABLE raw\.(Source\w+)\s*\((.*?)\n    \);', sql, re.S):
        fields = {}
        for line in body.splitlines():
            match = re.match(r'\s*(\w+)\s+(NVARCHAR\(\d+\)|DECIMAL\(\d+,\s*\d+\)|DATETIME2\(\d+\)|TIME\(\d+\)|DATE|INT|BIT)\s+(.*)', line)
            if match:
                col, kind, rest = match.groups()
                fields[col] = (kind, 'NOT NULL' in rest or 'PRIMARY KEY' in rest)
        schema[name] = fields
    return schema

SCHEMA = source_schema()
SYSTEM_COLUMNS = {'CreatedDate', 'ModifiedDate'}


def json_value(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (datetime, date, time, Decimal)):
        return str(value)
    return value.item() if hasattr(value, 'item') else value


def convert(value, kind, required):
    if value is None or pd.isna(value) or str(value).strip() == '':
        if required:
            raise ValueError('required value is missing')
        return None
    if kind.startswith('NVARCHAR'):
        result = str(value).strip()
        if len(result.encode('utf-16-le')) // 2 > int(re.search(r'\d+', kind)[0]):
            raise ValueError('text exceeds SQL column length')
        return result
    if kind in ('INT', 'BIT'):
        result = Decimal(str(value))
        if not result.is_finite() or result != result.to_integral_value():
            raise ValueError('expected an integer')
        result = int(result)
        if kind == 'BIT' and result not in (0, 1):
            raise ValueError('expected 0 or 1')
        if not -2147483648 <= result <= 2147483647:
            raise ValueError('outside SQL INT range')
        return result
    if kind.startswith('DECIMAL'):
        precision, scale = map(int, re.findall(r'\d+', kind))
        result = Decimal(str(value))
        if not result.is_finite() or abs(result) >= 10 ** (precision-scale):
            raise ValueError('outside SQL decimal range')
        if result != result.quantize(Decimal(10) ** -scale):
            raise ValueError('too many decimal places')
        return result
    if kind == 'DATE':
        return date.fromisoformat(str(value)[:10]) if isinstance(value, (date, datetime)) else date.fromisoformat(str(value))
    if kind.startswith('TIME'):
        return time.fromisoformat(str(value))
    if kind.startswith('DATETIME2'):
        return datetime.fromisoformat(str(value)).replace(tzinfo=None)
    raise ValueError(f'Unsupported SQL type: {kind}')


def validate(datasets):
    """Return typed accepted frames and one rejection per source row; no fabricated values."""
    if set(datasets) != set(KEYS):
        raise ValueError('Canonical input must provide all ten Source*.csv entities.')
    accepted = {}
    failures = {}

    def reject(table, index, reason):
        failures.setdefault((table, int(index)), []).append(reason)

    for table, original in datasets.items():
        required = set(SCHEMA[table]) - SYSTEM_COLUMNS
        missing = required - set(original.columns)
        extra = set(original.columns) - set(SCHEMA[table])
        if missing or extra:
            raise ValueError(f'{table} schema mismatch: missing={sorted(missing)}, extra={sorted(extra)}')
        records = []
        for idx, row in original.iterrows():
            out = {}
            for column in original.columns:
                try:
                    out[column] = convert(row[column], *SCHEMA[table][column])
                except (ValueError, InvalidOperation, OverflowError) as ex:
                    out[column] = None
                    reject(table, idx, f'{column}: {ex}')
            records.append(out)
        frame = pd.DataFrame(records, columns=original.columns, dtype=object)
        for _, group in frame.groupby(KEYS[table], dropna=False, sort=False):
            if len(group) > 1:
                if len(group.drop_duplicates()) > 1:
                    for idx in group.index:
                        reject(table, idx, 'Conflicting duplicate business key')
                else:
                    for idx in group.index[1:]:
                        reject(table, idx, 'Identical duplicate business key')
        accepted[table] = frame

    def active(table):
        return accepted[table].loc[[i for i in accepted[table].index if (table, i) not in failures]]

    def check(table, predicate, reason):
        for idx, row in active(table).iterrows():
            if not predicate(row):
                reject(table, idx, reason)

    check('SourceCalendar', lambda r: 1 <= r.DayOfWeek <= 7 and 1 <= r.MonthNumber <= 12 and
          r.YearNumber == r.CalendarDate.year and r.DayOfMonth == r.CalendarDate.day and
          r.MonthNumber == r.CalendarDate.month and r.QuarterNumber == (r.CalendarDate.month-1)//3+1 and
          r.DayOfWeek == r.CalendarDate.weekday()+1, 'Calendar attributes disagree with date')
    check('SourceSupplier', lambda r: r.LeadTimeDays >= 0 and 0 <= r.QualityRating <= 5, 'Invalid supplier measures')
    check('SourceProduct', lambda r: r.UnitCost >= 0 and r.BasePrice >= 0, 'Negative price/cost')
    check('SourceStore', lambda r: r.SquareFootage > 0, 'Store area must be positive')
    check('SourcePromotion', lambda r: 0 <= r.DiscountPercent <= 100 and r.EndDate >= r.StartDate, 'Invalid promotion range')
    check('SourceSalesTransaction', lambda r: r.TotalAmount >= 0, 'Negative transaction amount')
    check('SourceSalesTransactionLine', lambda r: r.LineNumber > 0 and r.Quantity > 0 and
          r.UnitPrice >= 0 and 0 <= r.DiscountAmount <= r.Quantity*r.UnitPrice and
          abs(r.LineTotalAmount-(r.Quantity*r.UnitPrice-r.DiscountAmount)) <= Decimal('0.0001'),
          'Invalid sales quantity, price, discount or line calculation')
    check('SourceInventory', lambda r: min(r.QuantityOnHand, r.QuantityOnOrder, r.ReorderPoint, r.SafetyStock) >= 0,
          'Negative inventory measure')
    check('SourceShipment', lambda r: r.QuantityOrdered > 0 and 0 <= r.QuantityReceived <= r.QuantityOrdered and
          r.PromisedDeliveryDate >= r.OrderDate and (r.ActualDeliveryDate is None or r.ActualDeliveryDate >= r.OrderDate) and
          r.ShipmentStatus in ('Delivered', 'Delayed', 'In-Transit', 'Cancelled'), 'Invalid shipment measures/dates/status')

    references = [
        ('SourceProduct','SourceSupplierID','SourceSupplier','SourceSupplierID'),
        ('SourceSalesTransaction','SourceStoreID','SourceStore','SourceStoreID'),
        ('SourceSalesTransaction','SourceCustomerID','SourceCustomer','SourceCustomerID'),
        ('SourceSalesTransaction','TransactionDate','SourceCalendar','CalendarDate'),
        ('SourceSalesTransactionLine','TransactionID','SourceSalesTransaction','TransactionID'),
        ('SourceSalesTransactionLine','SourceProductID','SourceProduct','SourceProductID'),
        ('SourceSalesTransactionLine','PromotionID','SourcePromotion','PromotionID'),
        ('SourceInventory','SourceProductID','SourceProduct','SourceProductID'),
        ('SourceInventory','SourceStoreID','SourceStore','SourceStoreID'),
        ('SourceInventory','SnapshotDate','SourceCalendar','CalendarDate'),
        ('SourceShipment','SourceProductID','SourceProduct','SourceProductID'),
        ('SourceShipment','SourceSupplierID','SourceSupplier','SourceSupplierID'),
        ('SourceShipment','SourceStoreID','SourceStore','SourceStoreID'),
        ('SourceShipment','OrderDate','SourceCalendar','CalendarDate'),
        ('SourceShipment','PromisedDeliveryDate','SourceCalendar','CalendarDate'),
        ('SourceShipment','ActualDeliveryDate','SourceCalendar','CalendarDate'),
    ]
    for table, column, parent, key in references:
        values = set(active(parent)[key])
        check(table, lambda r: r[column] is None or r[column] in values, f'Unresolved {column}')
    tx = active('SourceSalesTransaction').set_index('TransactionID')
    promos = active('SourcePromotion').set_index('PromotionID')
    joins = active('SourceCustomer').set_index('SourceCustomerID')['JoinDate'].to_dict()
    check('SourceSalesTransaction', lambda r: r.SourceCustomerID is None or joins[r.SourceCustomerID] <= r.TransactionDate,
          'Purchase predates customer registration')
    check('SourceSalesTransactionLine', lambda r: r.PromotionID is None or
          promos.loc[r.PromotionID].StartDate <= tx.loc[r.TransactionID].TransactionDate <= promos.loc[r.PromotionID].EndDate,
          'Promotion outside its effective dates')
    # Quarantine incomplete baskets, rather than loading partial transactions silently.
    totals = active('SourceSalesTransactionLine').groupby('TransactionID')['LineTotalAmount'].sum()
    check('SourceSalesTransaction', lambda r: r.TransactionID in totals and
          abs(totals[r.TransactionID]-r.TotalAmount) <= Decimal('0.0001'), 'Header-to-line reconciliation failed')
    valid_tx = set(active('SourceSalesTransaction')['TransactionID'])
    check('SourceSalesTransactionLine', lambda r: r.TransactionID in valid_tx, 'Transaction rejected or missing')
    rejects = []
    for (table, idx), reasons in sorted(failures.items()):
        rejects.append({'entity': table, 'row_number': idx+1, 'reason': '; '.join(reasons),
                        'payload': {c: json_value(v) for c, v in datasets[table].iloc[idx].items()}})
    return {t: active(t).copy() for t in accepted}, rejects
