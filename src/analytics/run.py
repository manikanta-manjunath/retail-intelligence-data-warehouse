"""Run defensible analytics against the verified SQL Server warehouse."""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.analytics.data import query, sales, signature, synthetic_anomaly_labels
from src.analytics.forecasting import complete_weeks, forecast
from src.analytics.mining import anomalies, basket_rules, customer_segmentation
from src.analytics.problems import detect_problems
from src.etl.verify import verify
from src.utils.config import PROJECT_ROOT, app_config


def _records(frame):
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def _promotion_analysis(sales_frame, window):
    daily = sales_frame.groupby("FullDate", as_index=False).agg(
        NetSales=("NetSalesAmount", "sum"),
        Discount=("DiscountAmount", "sum"),
        Transactions=("TransactionID", "nunique"),
    )
    daily["FullDate"] = pd.to_datetime(daily["FullDate"])
    promotions = query(
        """SELECT PromotionID,PromotionName,PromotionType,DiscountPercent,StartDate,EndDate
           FROM dw.DimPromotion WHERE PromotionKey<>0 ORDER BY StartDate"""
    )
    rows = []
    for promo in promotions.itertuples():
        start, end = pd.Timestamp(promo.StartDate), pd.Timestamp(promo.EndDate)
        during = daily[(daily.FullDate >= start) & (daily.FullDate <= end)]
        before = daily[
            (daily.FullDate >= start - pd.Timedelta(days=window))
            & (daily.FullDate < start)
        ]
        during_mean = during.NetSales.mean()
        baseline = before.NetSales.mean()
        rows.append(
            {
                "PromotionID": promo.PromotionID,
                "PromotionName": promo.PromotionName,
                "PromotionType": promo.PromotionType,
                "DiscountPercent": float(promo.DiscountPercent),
                "StartDate": str(start.date()),
                "EndDate": str(end.date()),
                "PromotionDailySales": float(during_mean) if pd.notna(during_mean) else None,
                "PriorWindowDailySales": float(baseline) if pd.notna(baseline) else None,
                "DescriptiveLiftPercent": (
                    float((during_mean / baseline - 1) * 100)
                    if pd.notna(during_mean) and pd.notna(baseline) and baseline
                    else None
                ),
                "PromotionDiscountAmount": float(during.Discount.sum()),
            }
        )
    return pd.DataFrame(rows)


def _inventory_analysis(sales_frame, config):
    demand = (
        sales_frame.groupby(["SourceProductID", "ProductName", "Category"])
        .agg(Revenue=("NetSalesAmount", "sum"), Units=("QuantitySold", "sum"))
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    demand["RevenueShare"] = demand.Revenue / demand.Revenue.sum()
    demand["CumulativeRevenueShare"] = demand.RevenueShare.cumsum()
    a, b = config["abc_thresholds"]["A"], config["abc_thresholds"]["B"]
    demand["ABCClass"] = np.select(
        [demand.CumulativeRevenueShare <= a, demand.CumulativeRevenueShare <= b],
        ["A", "B"],
        default="C",
    )
    weekly = (
        sales_frame.assign(
            Week=pd.to_datetime(sales_frame.FullDate).dt.to_period("W").dt.start_time
        )
        .groupby(["SourceProductID", "Week"])
        .QuantitySold.sum()
        .unstack(fill_value=0)
    )
    variation = pd.DataFrame(
        {
            "SourceProductID": weekly.index,
            "DemandCV": weekly.std(axis=1)
            / weekly.mean(axis=1).replace(0, np.nan),
        }
    ).reset_index(drop=True)
    x, y = config["xyz_thresholds"]["X"], config["xyz_thresholds"]["Y"]
    variation["XYZClass"] = np.select(
        [variation.DemandCV <= x, variation.DemandCV <= y],
        ["X", "Y"],
        default="Z",
    )
    latest = query(
        """SELECT * FROM dw.vw_InventoryPosition
           WHERE SnapshotDate=(SELECT MAX(SnapshotDate) FROM dw.vw_InventoryPosition)"""
    )
    return latest.merge(
        demand[
            [
                "SourceProductID",
                "Revenue",
                "Units",
                "RevenueShare",
                "CumulativeRevenueShare",
                "ABCClass",
            ]
        ],
        on="SourceProductID",
        how="left",
    ).merge(variation, on="SourceProductID", how="left")


def run():
    verification = verify()
    if not verification["passed"]:
        raise RuntimeError("Warehouse verification failed; analytics were not run.")
    cfg = app_config.model_config
    snapshot = signature()
    output = PROJECT_ROOT / "reports" / "generated" / "analytics"
    models = PROJECT_ROOT / "models" / "trained"
    output.mkdir(parents=True, exist_ok=True)
    models.mkdir(parents=True, exist_ok=True)

    detail = sales()
    detail["FullDate"] = pd.to_datetime(detail.FullDate)
    coverage = query("SELECT MIN(FullDate) AS StartDate,MAX(FullDate) AS EndDate FROM dw.DimDate").iloc[0]
    weekly = complete_weeks(detail, coverage.StartDate, coverage.EndDate)
    metadata, backtests, backtest_folds, test, predictions, future, forecast_bundle = forecast(
        weekly, cfg["forecasting"]
    )
    rules, rules_meta = basket_rules(detail, cfg["association_rules"])

    rfm = query("SELECT * FROM mart.vw_CustomerRFMSummary")
    segmented, profiles, segmentation_meta, segmentation_bundle = customer_segmentation(
        rfm, cfg["segmentation"]
    )
    anomaly_lines, anomaly_meta, anomaly_bundle = anomalies(
        detail, cfg["anomaly_detection"], synthetic_anomaly_labels()
    )
    problems = detect_problems(detail)
    inventory = _inventory_analysis(detail, cfg["inventory"])
    promotions = _promotion_analysis(
        detail, cfg["promotion"]["baseline_days_before"]
    )
    suppliers = query("SELECT * FROM mart.vw_SupplierDeliveryScorecard")

    outputs = {
        "forecast_backtest_metrics.csv": backtests,
        "forecast_backtest_folds.csv": backtest_folds,
        "forecast_test_metrics.csv": test,
        "forecast_test_predictions.csv": predictions,
        "forecast_future.csv": future,
        "association_rules.csv": rules,
        "customer_segments.csv": segmented,
        "customer_segment_profiles.csv": profiles,
        "sales_anomalies.csv": anomaly_lines,
        "detected_problems.csv": problems,
        "inventory_abc_xyz.csv": inventory,
        "promotion_analysis.csv": promotions,
        "supplier_scorecard.csv": suppliers,
    }
    for name, frame in outputs.items():
        frame.to_csv(output / name, index=False)

    joblib.dump(forecast_bundle, models / "weekly_sales_forecast.joblib")
    joblib.dump(segmentation_bundle, models / "customer_segmentation.joblib")
    joblib.dump(anomaly_bundle, models / "sales_anomaly_detector.joblib")
    selected_test = test[test.Model == metadata["selected_model"]].iloc[0].to_dict()
    report = {
        "status": "SUCCESS",
        "warehouse_signature": snapshot,
        "forecast": {
            **metadata,
            "selected_model_test_metrics": {
                key: (None if pd.isna(value) else float(value))
                for key, value in selected_test.items()
                if key != "Model"
            },
        },
        "association_rules": rules_meta,
        "segmentation": segmentation_meta,
        "anomaly_detection": anomaly_meta,
        "problems": {
            "detected_rows": len(problems),
            "problem_types": problems.ProblemType.value_counts().to_dict(),
        },
        "inventory": {
            "latest_snapshot_rows": len(inventory),
            "stockout_rows": int(inventory.StockoutFlag.sum()),
            "reorder_rows": int(inventory.UnderStockFlag.sum()),
            "limitations": [
                "Only 30 generated SKUs and five stores have daily inventory snapshots.",
                "ABC/XYZ classifications describe generated demand and are not replenishment policy recommendations.",
            ],
        },
        "promotion": {
            "promotions_evaluated": len(promotions),
            "limitations": [
                "Before/during comparison is descriptive and does not establish causal promotion lift.",
                "Promotions are generated and applied broadly in the canonical demonstration.",
            ],
        },
        "supplier": {
            "suppliers_evaluated": len(suppliers),
            "limitations": ["Shipment records are generated educational telemetry."],
        },
        "outputs": sorted(outputs),
    }
    (output / "analytics_report.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n"
    )
    return report
