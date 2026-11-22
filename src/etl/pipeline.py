"""Audited ingestion, repeatable dimension/fact loading and transactional reconciliation."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from src.db.connection import db_manager
from src.etl.validation import KEYS, validate, json_value
from src.utils.config import PROJECT_ROOT

DIMENSIONS = {'SourceProduct', 'SourceStore', 'SourceCustomer', 'SourceSupplier', 'SourcePromotion'}
FACTS = {'SourceSalesTransactionLine': 'FactSales', 'SourceInventory': 'FactInventorySnapshot', 'SourceShipment': 'FactShipment'}


def read_input(directory):
    path = Path(directory)
    manifest = json.loads((path/'manifest.json').read_text())
    if manifest.get('source_system') != 'SYNTHETIC_CANONICAL' or manifest.get('synthetic') is not True:
        raise ValueError('This canonical loader accepts declared synthetic data only. Public adapters preserve separate source grains.')
    datasets = {}
    for name in KEYS:
        source = path/f'{name}.csv'
        info = manifest['files'][name]
        if hashlib.sha256(source.read_bytes()).hexdigest() != info['sha256']:
            raise ValueError(f'{name}: source hash does not match manifest')
        frame = pd.read_csv(source, dtype=str, keep_default_na=False)
        if len(frame) != info['rows']:
            raise ValueError(f'{name}: row count does not match manifest')
        datasets[name] = frame
    return datasets, manifest


def read_anomaly_ground_truth(directory, manifest):
    """Read and authenticate optional synthetic anomaly labels from the manifest."""
    info = manifest.get('ground_truth_files', {}).get('sales_anomalies')
    if not info:
        return pd.DataFrame(columns=['TransactionID', 'LineNumber', 'AnomalyType'])
    source = Path(directory) / info['file']
    if not source.is_file():
        raise ValueError('sales anomaly ground-truth file declared in manifest is missing')
    if hashlib.sha256(source.read_bytes()).hexdigest() != info['sha256']:
        raise ValueError('sales anomaly ground-truth hash does not match manifest')
    frame = pd.read_csv(source, dtype={'TransactionID': str, 'LineNumber': int, 'AnomalyType': str})
    required = {'TransactionID', 'LineNumber', 'AnomalyType'}
    if set(frame.columns) != required:
        raise ValueError('sales anomaly ground truth has an unexpected schema')
    if len(frame) != info['rows']:
        raise ValueError('sales anomaly ground-truth row count does not match manifest')
    if frame.isna().any().any() or frame.duplicated(list(required)).any():
        raise ValueError('sales anomaly ground truth contains null or duplicate labels')
    return frame


def execute_result(cursor, sql, params=()):
    cursor.execute(sql, params)
    while cursor.description is None:
        if not cursor.nextset():
            raise RuntimeError('Expected result set from SQL')
    rows = cursor.fetchall()
    while cursor.nextset():
        pass
    return rows


def load(directory, manager=None):
    manager = manager or db_manager
    datasets, manifest = read_input(directory)
    accepted, rejected = validate(datasets)
    anomaly_truth = read_anomaly_ground_truth(directory, manifest)
    if not anomaly_truth.empty:
        accepted_keys = set(zip(
            accepted['SourceSalesTransactionLine'].TransactionID.astype(str),
            accepted['SourceSalesTransactionLine'].LineNumber.astype(int),
        ))
        truth_keys = set(zip(
            anomaly_truth.TransactionID.astype(str),
            anomaly_truth.LineNumber.astype(int),
        ))
        missing = truth_keys - accepted_keys
        if missing:
            raise ValueError(
                f'sales anomaly ground truth contains {len(missing)} transaction-line keys '
                'that are not present in accepted sales lines'
            )
    source_count = sum(map(len, datasets.values()))
    audit = manager.get_raw_connection(autocommit=True)
    ac = audit.cursor()
    run_id = execute_result(ac, "SET NOCOUNT ON; DECLARE @id INT; EXEC audit.usp_StartETLRun %s, %s, @id OUTPUT; SELECT @id;",
                            ('CanonicalRetail', 'INCREMENTAL'))[0][0]
    counts = {}
    updated = 0
    archive_conn = None
    archive_cursor = None
    conn = None
    cur = None
    try:
        ac.execute('INSERT INTO audit.IngestionManifest VALUES (%s,%s,%s)',
                   (run_id, manifest['source_system'], json.dumps(manifest)))
        archive_conn = manager.get_raw_connection()
        archive_cursor = archive_conn.cursor()
        # Archive every original row before the warehouse transaction, including invalid rows.
        for table, frame in datasets.items():
            archive = []
            for idx, row in frame.iterrows():
                payload = json.dumps({c: json_value(v) for c, v in row.items()}, sort_keys=True)
                archive.append((run_id, table, idx+1, manifest['source_system'],
                                hashlib.sha256(payload.encode()).hexdigest(), payload))
            for start in range(0, len(archive), 1000):
                archive_cursor.executemany('INSERT INTO raw.IngestedRecord (ETLRunID,EntityName,SourceRowNumber,SourceSystem,RecordHash,Payload) VALUES (%s,%s,%s,%s,%s,%s)', archive[start:start+1000])
        if rejected:
            archive_cursor.executemany('INSERT INTO audit.RejectedRecord VALUES (%s,%s,%s,%s,%s)',
                                       [(run_id, r['entity'], r['row_number'], r['reason'][:1000], json.dumps(r['payload'])) for r in rejected])
        archive_conn.commit()
        conn = manager.get_raw_connection()
        cur = conn.cursor()
        cur.execute('SET XACT_ABORT ON;')
        # Serialize warehouse writers; archive/audit remain observable during a failure.
        code = execute_result(cur, "DECLARE @r INT; EXEC @r=sp_getapplock @Resource='CanonicalRetailETL', @LockMode='Exclusive', @LockOwner='Transaction', @LockTimeout=10000; SELECT @r;")[0][0]
        if code < 0:
            raise RuntimeError('Another warehouse load holds the ETL lock')
        now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
        for table, original in accepted.items():
            frame = original.copy()
            columns = list(frame.columns)
            if table == 'SourceProduct':
                # Capture observed change time, not a new time on every replay.
                existing = execute_result(cur, 'SELECT SourceProductID, CreatedDate, ModifiedDate FROM raw.SourceProduct')
                times = {r[0]: (r[1], r[2]) for r in existing}
                frame['CreatedDate'] = [times.get(v, (now,now))[0] for v in frame.SourceProductID]
                frame['ModifiedDate'] = now
                columns = list(frame.columns)
            column_sql = ','.join('['+c+']' for c in columns)
            placeholders = ','.join(['%s']*(len(columns)+1))
            values = [tuple(json_value(v) if not isinstance(v, (datetime,)) else v for v in row)+(run_id,)
                      for row in frame.itertuples(index=False, name=None)]
            # Native date/time/Decimal values are preserved for SQL comparison and insertion.
            for start in range(0,len(values),1000):
                cur.executemany(f'INSERT INTO stg.{table} ({column_sql},ETLRunID) VALUES ({placeholders})',values[start:start+1000])
            join = ' AND '.join(f't.[{c}]=s.[{c}]' for c in KEYS[table])
            comparable = [c for c in columns if c not in KEYS[table] and c not in ('CreatedDate','ModifiedDate')]
            diff = ' OR '.join(f'(t.[{c}]<>s.[{c}] OR (t.[{c}] IS NULL AND s.[{c}] IS NOT NULL) OR (t.[{c}] IS NOT NULL AND s.[{c}] IS NULL))' for c in comparable) or '1=0'
            if table not in DIMENSIONS:
                conflicts = execute_result(cur, f'SELECT COUNT(*) FROM raw.{table} t JOIN stg.{table} s ON {join} WHERE s.ETLRunID=%s AND ({diff})', (run_id,))[0][0]
                if conflicts:
                    raise ValueError(f'{table}: {conflicts} existing business keys have changed immutable records; load aborted without replacing data.')
            else:
                assignments = ','.join(f't.[{c}]=s.[{c}]' for c in comparable)
                if table == 'SourceProduct':
                    assignments += ',t.ModifiedDate=s.ModifiedDate'
                rows = execute_result(cur, f'SET NOCOUNT ON; UPDATE t SET {assignments} FROM raw.{table} t JOIN stg.{table} s ON {join} WHERE s.ETLRunID=%s AND ({diff}); SELECT @@ROWCOUNT;', (run_id,))[0][0]
                updated += rows
            cur.execute(f'INSERT INTO raw.{table} ({column_sql}) SELECT '+','.join(f's.[{c}]' for c in columns)+f' FROM stg.{table} s WHERE s.ETLRunID=%s AND NOT EXISTS (SELECT 1 FROM raw.{table} t WHERE {join})', (run_id,))
            if table == 'SourceProduct':
                cur.execute('UPDATE s SET s.ModifiedDate=t.ModifiedDate FROM stg.SourceProduct s JOIN raw.SourceProduct t ON s.SourceProductID=t.SourceProductID WHERE s.ETLRunID=%s', (run_id,))
        for procedure in ['usp_LoadDimDate','usp_LoadDimProduct_SCD2','usp_LoadDimStore_SCD1','usp_LoadDimCustomer','usp_LoadDimAuxiliary']:
            cur.execute(f'EXEC dw.{procedure} @ETLRunID=%s', (run_id,))
            while cur.nextset():
                pass
        for procedure, table in [('usp_LoadFactSales','FactSales'),('usp_LoadFactInventorySnapshot','FactInventorySnapshot'),('usp_LoadFactShipment','FactShipment')]:
            extra = ', @SourceSystem=%s' if table == 'FactSales' else ''
            params = (run_id, manifest['source_system']) if extra else (run_id,)
            counts[table] = execute_result(cur, f'DECLARE @n INT; EXEC dw.{procedure} @ETLRunID=%s, @InsertedCount=@n OUTPUT{extra}; SELECT @n;', params)[0][0]
        if not anomaly_truth.empty:
            labels = [
                (manifest['source_system'], str(row.TransactionID), int(row.LineNumber),
                 str(row.AnomalyType), run_id)
                for row in anomaly_truth.itertuples(index=False)
            ]
            cur.executemany('''
                INSERT INTO audit.SyntheticAnomalyGroundTruth
                    (SourceSystem,TransactionID,TransactionLineID,AnomalyType,FirstSeenETLRunID)
                SELECT %s,%s,%s,%s,%s
                WHERE NOT EXISTS (
                    SELECT 1 FROM audit.SyntheticAnomalyGroundTruth
                    WHERE SourceSystem=%s AND TransactionID=%s
                      AND TransactionLineID=%s AND AnomalyType=%s
                )''', [row + row[:4] for row in labels])
        # Reconcile accepted business keys (including no-op replays), not just this run's inserted rows.
        sales_count, sales_total = execute_result(cur, '''SELECT COUNT(*), COALESCE(SUM(f.NetSalesAmount),0)
            FROM stg.SourceSalesTransactionLine s JOIN dw.FactSales f ON f.TransactionID=s.TransactionID AND f.TransactionLineID=s.LineNumber WHERE s.ETLRunID=%s''',(run_id,))[0]
        expected_total = sum(accepted['SourceSalesTransactionLine'].LineTotalAmount)
        if sales_count != len(accepted['SourceSalesTransactionLine']) or abs(sales_total-expected_total) > 0.0001:
            raise RuntimeError('Sales source-to-target reconciliation failed')
        inv_count = execute_result(cur, '''SELECT COUNT(*) FROM stg.SourceInventory s JOIN dw.DimProduct p ON p.SourceProductID=s.SourceProductID
            AND s.SnapshotDate>=p.EffectiveFrom AND (p.EffectiveTo IS NULL OR s.SnapshotDate<p.EffectiveTo)
            JOIN dw.DimStore d ON d.SourceStoreID=s.SourceStoreID AND d.IsCurrent=1 JOIN dw.FactInventorySnapshot f
            ON f.DateKey=CONVERT(INT,CONVERT(CHAR(8),s.SnapshotDate,112)) AND f.ProductKey=p.ProductKey AND f.StoreKey=d.StoreKey WHERE s.ETLRunID=%s''',(run_id,))[0][0]
        shipment_count = execute_result(cur, 'SELECT COUNT(*) FROM stg.SourceShipment s JOIN dw.FactShipment f ON f.ShipmentID=s.ShipmentID WHERE s.ETLRunID=%s',(run_id,))[0][0]
        if inv_count != len(accepted['SourceInventory']) or shipment_count != len(accepted['SourceShipment']):
            raise RuntimeError('Inventory/shipment source-to-target reconciliation failed')
        for table, frame in accepted.items():
            rejected_count = sum(r['entity']==table for r in rejected)
            cur.execute('INSERT INTO audit.DataQualityLog (ETLRunID,TableName,CheckType,CheckDescription,RecordsFailed,Severity,Status) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                        (run_id, table, 'VALIDATION', 'Types, grain, ranges, reference and basket checks', rejected_count,
                         'WARNING' if rejected_count else 'INFO', 'FAILED' if rejected_count else 'PASSED'))
        cur.execute("INSERT INTO audit.DataQualityLog (ETLRunID,TableName,CheckType,CheckDescription,Status) VALUES (%s,'dw facts','RECONCILIATION','Accepted keys and sales totals reconcile','PASSED')",(run_id,))
        cur.execute('EXEC audit.usp_EndETLRun %s,%s,%s,%s,%s,%s,%s',
                   (run_id, 'SUCCESS', source_count, sum(counts.values()), updated, len(rejected), None))
        conn.commit()
    except Exception as ex:
        if archive_conn is not None:
            archive_conn.rollback()
        if conn is not None:
            conn.rollback()
        ac.execute('EXEC audit.usp_EndETLRun %s,%s,%s,%s,%s,%s,%s',
                   (run_id,'FAILED',source_count,0,0,len(rejected),str(ex)[:2000]))
        raise
    finally:
        if archive_cursor is not None:
            archive_cursor.close()
        if archive_conn is not None:
            archive_conn.close()
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
        ac.close()
        audit.close()
    report = {'run_id': run_id, 'status': 'SUCCESS', 'source_rows': source_count,
              'accepted_rows': sum(map(len,accepted.values())), 'rejected_rows': len(rejected),
              'inserted_facts': counts, 'updated_source_dimensions': updated,
              'net_sales_reconciled': str(sales_total), 'source_system': manifest['source_system']}
    report['synthetic_anomaly_labels'] = len(anomaly_truth)
    out = PROJECT_ROOT/'reports/generated'; out.mkdir(parents=True,exist_ok=True)
    (out/f'etl_run_{run_id}.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
