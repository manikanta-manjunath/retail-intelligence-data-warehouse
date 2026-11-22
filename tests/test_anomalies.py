import numpy as np
import pandas as pd

from src.analytics.mining import anomalies


def test_synthetic_precision_recall_and_chronological_split():
    count = 500
    dates = pd.date_range('2020-01-01', periods=count, freq='D')
    rng = np.random.default_rng(42)
    quantity = rng.choice([1.0, 2.0, 3.0], size=count, p=[0.8, 0.15, 0.05])
    price = rng.normal(10.0, 0.5, size=count)
    quantity[[420, 440, 460, 480]] = 25
    sales = pd.DataFrame({
        'TransactionID': [f'TX-{i}' for i in range(count)],
        'TransactionLineID': 1,
        'FullDate': dates,
        'SourceProductID': 'P1',
        'ProductName': 'Product',
        'Category': 'Category',
        'SourceStoreID': 'S1',
        'QuantitySold': quantity,
        'UnitPrice': price,
        'NetSalesAmount': quantity * price,
        'DiscountAmount': 0.0,
    })
    labels = pd.DataFrame({
        'TransactionID': [f'TX-{i}' for i in [420, 440, 460, 480]],
        'TransactionLineID': 1,
        'AnomalyType': 'INJECTED_HIGH_QUANTITY',
    })
    cfg = {'features':['QuantitySold','UnitPrice','NetSalesAmount','DiscountAmount'],
           'contamination':0.02,'chronological_train_fraction':0.8,'random_state':42}
    output, metadata, _ = anomalies(sales, cfg, labels)
    assert metadata['training_cutoff'] == '2021-02-03'
    assert metadata['synthetic_positive_lines'] == 4
    assert metadata['true_positives'] == 4
    assert metadata['precision'] is not None
    assert metadata['recall'] == 1.0
    assert output.IsSyntheticInjectedAnomaly.sum() == 4
