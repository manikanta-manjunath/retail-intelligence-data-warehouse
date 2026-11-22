import json
import pandas as pd
import pytest

from src.ingestion.adapters import adapt_uci_online_retail, adapt_walmart_weekly_sales


def test_walmart_adapter_preserves_weekly_grain(tmp_path):
    train = tmp_path / "train.csv"
    features = tmp_path / "features.csv"
    stores = tmp_path / "stores.csv"
    pd.DataFrame({
        "Store": [1, 1], "Dept": [1, 2], "Date": ["2012-01-06"] * 2,
        "Weekly_Sales": [100.0, -5.0], "IsHoliday": [False, False],
    }).to_csv(train, index=False)
    pd.DataFrame({
        "Store": [1], "Date": ["2012-01-06"], "IsHoliday": [False],
        "Temperature": [42.0],
    }).to_csv(features, index=False)
    pd.DataFrame({"Store": [1], "Type": ["A"], "Size": [100000]}).to_csv(stores, index=False)
    frame, manifest = adapt_walmart_weekly_sales(
        train, tmp_path / "out", features, stores
    )
    assert len(frame) == 2
    assert frame.Weekly_Sales.min() == -5.0
    assert manifest["grain"].startswith("one weekly")
    assert manifest["synthetic"] is False


def test_walmart_adapter_rejects_duplicate_grain(tmp_path):
    source = tmp_path / "train.csv"
    row = {"Store": 1, "Dept": 1, "Date": "2012-01-06",
           "Weekly_Sales": 1, "IsHoliday": False}
    pd.DataFrame([row, row]).to_csv(source, index=False)
    with pytest.raises(ValueError, match="grain"):
        adapt_walmart_weekly_sales(source, tmp_path / "out")


def test_uci_adapter_preserves_cancellations_and_rejects_invalid(tmp_path):
    source = tmp_path / "uci.csv"
    pd.DataFrame({
        "Invoice": ["100", "C101", ""],
        "StockCode": ["A", "B", "C"],
        "Description": ["One", "Return", "Invalid"],
        "Quantity": [2, -1, 0],
        "InvoiceDate": ["2010-01-01 10:00"] * 3,
        "Price": [3.5, 4.0, 1.0],
        "Customer ID": [1, 1, None],
        "Country": ["United Kingdom"] * 3,
    }).to_csv(source, index=False)
    frame, manifest = adapt_uci_online_retail(source, tmp_path / "out")
    assert len(frame) == 2
    assert frame.IsCancellation.tolist() == [False, True]
    assert manifest["rejected_rows"] == 1
    assert (tmp_path / "out" / "rejected_rows.csv").exists()
