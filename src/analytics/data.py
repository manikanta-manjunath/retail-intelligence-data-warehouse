"""Read verified warehouse data and identify the snapshot behind model outputs."""
import json
import pandas as pd
from sqlalchemy import text
from src.db.connection import db_manager


def query(sql, params=None):
    engine=db_manager.get_engine()
    try:
        with engine.connect() as conn:
            return pd.read_sql_query(text(sql),conn,params=params or {})
    finally:
        engine.dispose()


def signature():
    row=query('''SELECT (SELECT MAX(ETLRunID) FROM audit.ETLRunHistory WHERE Status='SUCCESS') AS SuccessfulRun,
        COUNT_BIG(*) AS SalesLines, COALESCE(SUM(NetSalesAmount),0) AS NetSales,
        COALESCE(MAX(SalesFactKey),0) AS LastSalesKey,
        (SELECT COUNT_BIG(*) FROM dw.FactInventorySnapshot) AS InventoryRows,
        (SELECT COUNT_BIG(*) FROM dw.FactShipment) AS Shipments,
        (SELECT COUNT_BIG(*) FROM dw.DimProduct) AS ProductVersions FROM dw.FactSales''').iloc[0]
    return {k:str(v) for k,v in row.items()}


def sales():
    return query('''SELECT TransactionID,TransactionLineID,FullDate,SourceProductID,ProductName,Category,
        SourceStoreID,StoreName,StoreState,ChannelName,SourceCustomerID,QuantitySold,UnitPrice,
        GrossSalesAmount,DiscountAmount,NetSalesAmount,CostAmount,ProfitAmount,
        PromotionName,PromotionType,HolidayFlag FROM dw.vw_SalesDetail''')


def synthetic_anomaly_labels():
    return query('''SELECT TransactionID,TransactionLineID,AnomalyType
        FROM audit.SyntheticAnomalyGroundTruth''')
