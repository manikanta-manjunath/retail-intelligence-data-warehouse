import subprocess
import sys
from datetime import date

import pytest
from streamlit.testing.v1 import AppTest
from src.utils.config import PROJECT_ROOT


def test_dashboard_entrypoint_resolves_project_package():
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "dashboard" / "app.py")],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.integration
def test_dashboard_executes_all_sections():
    app = AppTest.from_file(PROJECT_ROOT / "dashboard" / "app.py").run(timeout=60)
    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Executive",
        "Products & stores",
        "Forecast",
        "Basket & customers",
        "Inventory & suppliers",
        "Problems & precision",
        "Anomalies & ETL",
    ]
    assert len(app.metric) == 20
    assert len(app.dataframe) == 9

    app.date_input[0].set_value((date(2024, 1, 1), date(2024, 12, 31)))
    app.run(timeout=60)
    assert not app.exception
    assert any('select at least 128 weeks' in notice.value for notice in app.info)
