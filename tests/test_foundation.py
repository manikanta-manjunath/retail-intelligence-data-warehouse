import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
import pandas as pd
import pytest
from src.db.executor import SQLExecutor, split_batches
from src.etl.pipeline import read_anomaly_ground_truth, read_input
from src.etl.validation import validate
from src.ingestion.generator import RetailDataGenerator


@pytest.fixture
def canonical(tmp_path):
    generator = RetailDataGenerator()
    generator.target_transactions = 140
    generator.num_products = 30
    generator.num_stores = 2
    generator.num_suppliers = 3
    generator.num_customers = 10
    frames = generator.generate_all(str(tmp_path/'input'))
    return frames, tmp_path/'input'


def test_calendar_and_registration(canonical):
    frames, _ = canonical
    cal = frames['SourceCalendar'].set_index('CalendarDate')
    from datetime import date
    assert cal.loc[date(2024,11,28),'HolidayName'] == 'Thanksgiving Day'
    assert cal.loc[date(2024,11,29),'HolidayName'] == 'Black Friday'
    assert cal.loc[date(2024,11,23),'IsHoliday'] == 0
    valid, rejects = validate(frames)
    assert not rejects
    assert len(valid['SourceInventory']) == 60*2*30


def test_hash_integrity(canonical):
    _, path = canonical
    frames, manifest = read_input(path)
    assert manifest['synthetic'] is True
    with (path/'SourceStore.csv').open('a') as handle:
        handle.write('\n')
    with pytest.raises(ValueError, match='hash'):
        read_input(path)


def test_negative_line_quarantines_basket(canonical):
    frames, _ = canonical
    frames['SourceSalesTransactionLine'].loc[0,'Quantity'] = -1
    tx_id = frames['SourceSalesTransactionLine'].loc[0,'TransactionID']
    valid, rejects = validate(frames)
    assert tx_id not in set(valid['SourceSalesTransaction'].TransactionID)
    assert tx_id not in set(valid['SourceSalesTransactionLine'].TransactionID)
    assert any('quantity' in r['reason'] for r in rejects)


def test_identical_duplicates_are_logged(canonical):
    frames, _ = canonical
    original = frames['SourceProduct']
    frames['SourceProduct'] = pd.concat([original, original.iloc[[0]]],ignore_index=True)
    valid, rejects = validate(frames)
    assert len(valid['SourceProduct']) == len(original)
    assert any('Identical duplicate' in r['reason'] for r in rejects)


def test_conflicting_dimension_rejects_dependents(canonical):
    frames, _ = canonical
    product = frames['SourceProduct'].iloc[[0]].copy()
    product['BasePrice'] = 100
    frames['SourceProduct'] = pd.concat([frames['SourceProduct'],product],ignore_index=True)
    valid, rejects = validate(frames)
    assert product.iloc[0].SourceProductID not in set(valid['SourceProduct'].SourceProductID)
    assert product.iloc[0].SourceProductID not in set(valid['SourceInventory'].SourceProductID)


def test_orphan_and_bad_decimal_rejected(canonical):
    frames, _ = canonical
    frames['SourceSalesTransactionLine'].loc[0,'SourceProductID'] = 'MISSING'
    frames['SourceProduct']['BasePrice'] = frames['SourceProduct']['BasePrice'].astype(object)
    frames['SourceProduct'].loc[1,'BasePrice'] = Decimal('1.00001')
    _, rejected = validate(frames)
    assert any('Unresolved SourceProductID' in r['reason'] for r in rejected)
    assert any('decimal places' in r['reason'] for r in rejected)


def test_existing_output_preserved(canonical):
    _, path = canonical
    with pytest.raises(FileExistsError):
        RetailDataGenerator().generate_all(str(path))


def test_historical_mode_prefixes_keys_promotions_and_truth(tmp_path):
    generator = RetailDataGenerator('historical_15y')
    generator.target_transactions = 280
    generator.num_products = 30
    generator.num_stores = 2
    generator.num_suppliers = 3
    generator.num_customers = 10
    generator.num_shipments = 20
    generator.anomaly_rate = 0.25
    frames = generator.generate_all(str(tmp_path / 'historical'))
    assert frames['SourceSalesTransaction'].TransactionID.str.startswith('HIST-TX-').all()
    assert frames['SourceShipment'].ShipmentID.str.startswith('HIST-SHIP-').all()
    assert frames['SourcePromotion'].PromotionID.str.startswith('HIST-PROMO-').all()
    assert len(frames['SourcePromotion']) == 13 * 3
    _, manifest = read_input(tmp_path / 'historical')
    truth = read_anomaly_ground_truth(tmp_path / 'historical', manifest)
    assert not truth.empty
    assert set(zip(truth.TransactionID, truth.LineNumber)).issubset(
        set(zip(frames['SourceSalesTransactionLine'].TransactionID,
                frames['SourceSalesTransactionLine'].LineNumber))
    )


def test_ground_truth_hash_is_verified(tmp_path):
    generator = RetailDataGenerator('historical_15y')
    generator.target_transactions = 56
    generator.num_products = 30
    generator.num_stores = 2
    generator.num_suppliers = 3
    generator.num_customers = 10
    generator.num_shipments = 2
    generator.anomaly_rate = 1.0
    path = tmp_path / 'historical'
    generator.generate_all(str(path))
    _, manifest = read_input(path)
    with (path / 'ground_truth_sales_anomalies.csv').open('a') as handle:
        handle.write('\n')
    with pytest.raises(ValueError, match='ground-truth hash'):
        read_anomaly_ground_truth(path, manifest)


def test_seed_is_stable_between_processes(tmp_path):
    code = '''from src.ingestion.generator import RetailDataGenerator
import sys
x=RetailDataGenerator(); x.target_transactions=28; x.num_products=30; x.num_customers=5; x.num_stores=2; x.num_suppliers=3
x.generate_all(sys.argv[1])'''
    for seed in ('1','987'):
        subprocess.run([sys.executable,'-c',code,str(tmp_path/seed)],check=True,
                       env={**os.environ,'PYTHONHASHSEED':seed},capture_output=True)
    assert {p.name:p.read_bytes() for p in (tmp_path/'1').glob('*.csv')} == {p.name:p.read_bytes() for p in (tmp_path/'987').glob('*.csv')}


def test_setup_excludes_data_mutations():
    class RecordingExecutor(SQLExecutor):
        def __init__(self): self.scripts=[]
        def execute_script(self,path,database=None): self.scripts.append(Path(path).name)
    runner=RecordingExecutor(); runner.run_all_setup_scripts()
    assert '11_scd_type2_examples.sql' not in runner.scripts
    assert '13_reset_demo_data.sql' not in runner.scripts
    assert '12_reporting_queries.sql' not in runner.scripts
    assert runner.scripts.index('14_etl_reliability.sql') < runner.scripts.index('06_create_etl_procedures.sql')


def test_setup_propagates_sql_errors():
    class Cursor:
        def execute(self,sql): raise RuntimeError('SQL failed')
        def close(self): pass
    class Connection:
        def cursor(self): return Cursor()
        def close(self): pass
    class Manager:
        database='RetailIntelligenceDW'
        def get_raw_connection(self,*args,**kwargs):
            assert kwargs['autocommit'] is True
            return Connection()
    with pytest.raises(RuntimeError,match='SQL failed'):
        SQLExecutor(Manager()).execute_script('sql/01_create_schemas.sql')


def test_go_delimiters():
    assert split_batches('SELECT 1;\nGO -- comment\nSELECT 2;\ngo\n') == ['SELECT 1;','SELECT 2;']
