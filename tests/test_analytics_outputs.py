import json
from pathlib import Path

import pandas as pd
import pytest

from src.utils.config import PROJECT_ROOT


@pytest.mark.integration
def test_analytics_artifacts_are_traceable_and_coherent():
    root = PROJECT_ROOT / "reports" / "generated" / "analytics"
    report = json.loads((root / "analytics_report.json").read_text())
    assert report["status"] == "SUCCESS"
    assert int(float(report["warehouse_signature"]["SalesLines"])) == 182176
    assert report["forecast"]["selected_model_test_metrics"]["MASE"] < 1
    assert report["association_rules"]["basket_count"] == 73213
    assert report["forecast"]["backtest_folds"] == 5
    assert report["anomaly_detection"]["synthetic_positive_lines"] > 0
    assert 0 <= report["anomaly_detection"]["precision"] <= 1
    assert 0 <= report["anomaly_detection"]["recall"] <= 1
    rules = pd.read_csv(root / "association_rules.csv")
    assert len(rules) == report["association_rules"]["rule_count"]
    assert (rules.Lift > 1).all()
    future = pd.read_csv(root / "forecast_future.csv")
    assert len(future) == 12
    assert pd.to_datetime(future.WeekStart).min() > pd.Timestamp(
        report["forecast"]["test_end"]
    )
    for name in report["outputs"]:
        assert (root / name).is_file()
    problems = pd.read_csv(root / 'detected_problems.csv')
    assert {'SALES_SPIKE','STOCKOUT','SUPPLIER_DELAY'}.issubset(set(problems.ProblemType))
