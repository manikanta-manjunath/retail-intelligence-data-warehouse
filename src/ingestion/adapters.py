"""Public dataset adapters that preserve source grain and provenance."""
import hashlib
import json
from pathlib import Path

import pandas as pd


def _read(path, all_sheets=False):
    path = Path(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        if all_sheets:
            sheets = pd.read_excel(path, sheet_name=None)
            return pd.concat(sheets.values(), ignore_index=True)
        return pd.read_excel(path)
    return pd.read_csv(path)


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write(frame, output, name, manifest):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    target = output / name
    if target.exists() or (output / "manifest.json").exists():
        raise FileExistsError(f"Preserving existing adapter output in {output}")
    frame.to_csv(target, index=False)
    manifest["output_file"] = name
    manifest["output_rows"] = len(frame)
    manifest["output_sha256"] = _hash(target)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return frame, manifest


def adapt_walmart_weekly_sales(train_path, output, features_path=None, stores_path=None):
    """Normalize Kaggle Walmart weekly store-department rows without inventing baskets."""
    train = _read(train_path)
    required = {"Store", "Dept", "Date", "Weekly_Sales", "IsHoliday"}
    missing = required - set(train.columns)
    if missing:
        raise ValueError(f"Walmart train file is missing {sorted(missing)}")
    frame = train.copy()
    frame["Date"] = pd.to_datetime(frame.Date, errors="raise").dt.date
    frame["Store"] = pd.to_numeric(frame.Store, errors="raise").astype(int)
    frame["Dept"] = pd.to_numeric(frame.Dept, errors="raise").astype(int)
    frame["Weekly_Sales"] = pd.to_numeric(frame.Weekly_Sales, errors="raise")
    frame["IsHoliday"] = frame.IsHoliday.astype(str).str.lower().map(
        {"true": True, "false": False, "1": True, "0": False}
    )
    if frame.IsHoliday.isna().any():
        raise ValueError("Walmart IsHoliday contains unsupported values")
    if frame.duplicated(["Store", "Dept", "Date"]).any():
        raise ValueError("Walmart weekly Store/Dept/Date grain is not unique")
    inputs = {"train": {"path": str(train_path), "sha256": _hash(train_path)}}
    if features_path:
        features = _read(features_path)
        features["Date"] = pd.to_datetime(features.Date, errors="raise").dt.date
        if features.duplicated(["Store", "Date"]).any():
            raise ValueError("Walmart feature Store/Date grain is not unique")
        frame = frame.merge(features, on=["Store", "Date", "IsHoliday"], how="left", validate="many_to_one")
        inputs["features"] = {"path": str(features_path), "sha256": _hash(features_path)}
    if stores_path:
        stores = _read(stores_path)
        if stores.duplicated(["Store"]).any():
            raise ValueError("Walmart store key is not unique")
        frame = frame.merge(stores, on="Store", how="left", validate="many_to_one")
        inputs["stores"] = {"path": str(stores_path), "sha256": _hash(stores_path)}
    manifest = {
        "dataset": "Walmart Recruiting - Store Sales Forecasting",
        "source_system": "PUBLIC_KAGGLE_WALMART_WEEKLY",
        "synthetic": False,
        "grain": "one weekly sales observation per store and department",
        "license": "Kaggle competition rules; user must confirm eligibility and terms",
        "inputs": inputs,
        "limitations": [
            "Weekly aggregates are not transaction baskets.",
            "The dataset has no customer, supplier, line-item or inventory-position grain.",
            "Negative weekly sales may represent returns and are preserved.",
        ],
    }
    return _write(frame, output, "walmart_weekly_sales.csv", manifest)


def adapt_uci_online_retail(path, output):
    """Normalize UCI Online Retail/Online Retail II invoice lines and flag cancellations."""
    source = _read(path, all_sheets=True)
    aliases = {
        "Invoice": "InvoiceNo",
        "Invoice No": "InvoiceNo",
        "StockCode": "StockCode",
        "Stock Code": "StockCode",
        "Description": "Description",
        "Quantity": "Quantity",
        "InvoiceDate": "InvoiceDate",
        "Invoice Date": "InvoiceDate",
        "Price": "UnitPrice",
        "UnitPrice": "UnitPrice",
        "Customer ID": "CustomerID",
        "CustomerID": "CustomerID",
        "Country": "Country",
    }
    frame = source.rename(columns={c: aliases[c] for c in source.columns if c in aliases})
    required = {"InvoiceNo", "StockCode", "Quantity", "InvoiceDate", "UnitPrice", "Country"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"UCI file is missing {sorted(missing)}")
    if "CustomerID" not in frame:
        frame["CustomerID"] = pd.NA
    if "Description" not in frame:
        frame["Description"] = pd.NA
    frame["InvoiceNo"] = frame.InvoiceNo.astype(str).str.strip()
    frame["StockCode"] = frame.StockCode.astype(str).str.strip()
    frame["InvoiceDate"] = pd.to_datetime(frame.InvoiceDate, errors="coerce")
    frame["Quantity"] = pd.to_numeric(frame.Quantity, errors="coerce")
    frame["UnitPrice"] = pd.to_numeric(frame.UnitPrice, errors="coerce")
    invalid = (
        frame.InvoiceNo.eq("")
        | frame.StockCode.eq("")
        | frame.InvoiceDate.isna()
        | frame.Quantity.isna()
        | frame.UnitPrice.isna()
        | frame.Quantity.eq(0)
        | frame.UnitPrice.lt(0)
    )
    rejected = frame[invalid].copy()
    frame = frame[~invalid].copy()
    frame["IsCancellation"] = frame.InvoiceNo.str.upper().str.startswith("C") | frame.Quantity.lt(0)
    frame["LineAmount"] = frame.Quantity * frame.UnitPrice
    frame.insert(0, "SourceRowNumber", frame.index + 2)
    if frame.duplicated(["SourceRowNumber"]).any():
        raise ValueError("UCI source row identifiers are not unique")
    output = Path(output)
    normalized, manifest = _write(
        frame,
        output,
        "uci_online_retail_lines.csv",
        {
            "dataset": "UCI Online Retail / Online Retail II",
            "source_system": "PUBLIC_UCI_ONLINE_RETAIL",
            "synthetic": False,
            "grain": "one source invoice line, identified by original row number",
            "license": "CC BY 4.0 for Online Retail II; verify the exact downloaded edition",
            "inputs": {"source": {"path": str(path), "sha256": _hash(path)}},
            "rejected_rows": len(rejected),
            "limitations": [
                "Single-channel UK-based online retail data.",
                "Cancellations and returns remain distinguishable and are not silently deleted.",
                "No physical-store inventory, promotion or supplier telemetry is available.",
            ],
        },
    )
    if not rejected.empty:
        rejected.to_csv(output / "rejected_rows.csv", index=False)
    return normalized, manifest
