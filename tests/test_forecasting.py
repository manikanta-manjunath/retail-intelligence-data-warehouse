import numpy as np
import pandas as pd

from src.analytics.forecasting import forecast, minimum_history_weeks


def test_minimum_history_uses_defaults_for_stale_dashboard_config():
    assert minimum_history_weeks({'test_size_weeks': 12}) == 128


def test_rolling_backtests_are_chronological_and_select_before_test():
    index = pd.date_range('2010-01-04', periods=260, freq='W-MON')
    values = 1000 + np.arange(260) * 2 + 80 * np.sin(np.arange(260) * 2 * np.pi / 52)
    series = pd.Series(values, index=index)
    cfg = {
        'forecast_horizon_weeks': 12,
        'test_size_weeks': 12,
        'backtest_folds': 5,
        'minimum_train_weeks': 104,
        'lags': [1, 2, 4, 8, 12],
        'rolling_windows': [4, 8, 12],
        'models': ['naive', 'moving_average'],
        'random_state': 42,
    }
    metadata, summary, folds, test, predictions, future, _ = forecast(series, cfg)
    assert metadata['backtest_folds'] == 5
    assert set(summary.Model) == {'naive', 'moving_average'}
    assert summary.Folds.eq(5).all()
    assert pd.to_datetime(folds.TrainEnd).lt(pd.to_datetime(folds.ValidationStart)).all()
    assert pd.to_datetime(folds.ValidationEnd).max() < pd.Timestamp(metadata['test_start'])
    assert len(test) == 2
    assert len(predictions) == 24
    assert len(future) == 12
