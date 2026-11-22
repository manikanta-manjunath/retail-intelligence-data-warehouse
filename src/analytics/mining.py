"""Transaction baskets, synthetic-customer RFM clustering and unsupervised sales anomalies."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from mlxtend.frequent_patterns import fpgrowth, association_rules


def basket_rules(sales,cfg):
    baskets=sales[['TransactionID','SourceProductID']].drop_duplicates().assign(present=True).pivot(index='TransactionID',columns='SourceProductID',values='present').fillna(False).astype(bool)
    frequent=fpgrowth(baskets,min_support=cfg['min_support'],use_colnames=True,max_len=cfg['max_len'])
    columns=['Antecedents','Consequents','Support','Confidence','Lift']
    if frequent.empty or not (frequent.itemsets.map(len)>1).any():
        return pd.DataFrame(columns=columns),{'basket_count':len(baskets),'frequent_itemsets':len(frequent),'rule_count':0,'min_support':cfg['min_support']}
    rules=association_rules(frequent,metric='confidence',min_threshold=cfg['min_confidence'],num_itemsets=len(baskets))
    rules=rules[rules.lift>=cfg['min_lift']].sort_values(['lift','confidence'],ascending=False)
    out=pd.DataFrame({'Antecedents':rules.antecedents.map(lambda x:', '.join(sorted(x))),
                      'Consequents':rules.consequents.map(lambda x:', '.join(sorted(x))),
                      'Support':rules.support,'Confidence':rules.confidence,'Lift':rules.lift})
    return out,{'basket_count':len(baskets),'frequent_itemsets':len(frequent),'rule_count':len(out),'min_support':cfg['min_support'],
                'limitations':['Associations were embedded by the synthetic generator; these are demonstration results.','Transaction IDs are valid baskets; anonymous transactions remain included.']}


def customer_segmentation(rfm,cfg):
    columns=['RecencyDays','Frequency','Monetary']
    values=rfm[columns].astype(float)
    if len(values)<=cfg['n_clusters']:
        raise ValueError('Too few customers for configured segmentation')
    scaler=StandardScaler(); x=scaler.fit_transform(np.log1p(values))
    model=KMeans(n_clusters=cfg['n_clusters'],n_init=20,random_state=cfg['random_state']).fit(x)
    out=rfm.copy(); out['Cluster']=model.labels_
    profile=out.groupby('Cluster').agg(Customers=('SourceCustomerID','count'),MeanRecencyDays=('RecencyDays','mean'),MeanFrequency=('Frequency','mean'),MeanMonetary=('Monetary','mean')).reset_index()
    score=float(silhouette_score(x,model.labels_)) if 1<len(set(model.labels_))<len(x) else None
    return out,profile,{'silhouette_score':score,'customers_clustered':len(out),'clusters':cfg['n_clusters'],
                       'limitations':['Synthetic customer IDs only; anonymous sales excluded.','Unsupervised descriptive clusters; no classification accuracy or customer targeting claim.']},{'model':model,'scaler':scaler,'features':columns}


def anomalies(sales,cfg,labels=None):
    cols=cfg['features']; data=sales[cols].astype(float)
    labels = labels if labels is not None else pd.DataFrame(
        columns=['TransactionID','TransactionLineID','AnomalyType']
    )
    truth_keys = set(zip(
        labels.TransactionID.astype(str), labels.TransactionLineID.astype(int)
    )) if not labels.empty else set()
    dates = pd.to_datetime(sales.FullDate)
    unique_dates = np.array(sorted(dates.dropna().unique()))
    fraction = float(cfg.get('chronological_train_fraction', 0.80))
    split_index = min(len(unique_dates) - 2, max(0, int(len(unique_dates) * fraction) - 1))
    split = pd.Timestamp(unique_dates[split_index])
    labeled = pd.Series(
        [(str(tx), int(line)) in truth_keys
         for tx, line in zip(sales.TransactionID, sales.TransactionLineID)],
        index=sales.index,
    )
    train=(dates<=split) & ~labeled
    if train.sum()<50 or (~train).sum()<10:
        raise ValueError('Insufficient chronological anomaly training/evaluation records')
    scaler=StandardScaler(); model=IsolationForest(contamination=cfg['contamination'],n_estimators=120,random_state=cfg['random_state'],n_jobs=1)
    model.fit(scaler.fit_transform(data.loc[train]))
    evaluation=dates>split
    out=sales.loc[evaluation,['TransactionID','TransactionLineID','FullDate','SourceProductID','ProductName','Category','SourceStoreID','NetSalesAmount']].copy()
    x=scaler.transform(data.loc[evaluation]); out['AnomalyScore']=model.decision_function(x); out['IsAnomaly']=model.predict(x)==-1
    out['IsSyntheticInjectedAnomaly'] = [
        (str(tx), int(line)) in truth_keys
        for tx, line in zip(out.TransactionID, out.TransactionLineID)
    ]
    type_by_key = {
        (str(row.TransactionID), int(row.TransactionLineID)): row.AnomalyType
        for row in labels.itertuples(index=False)
    }
    out['SyntheticAnomalyType'] = [
        type_by_key.get((str(tx), int(line)))
        for tx, line in zip(out.TransactionID, out.TransactionLineID)
    ]
    predicted = out.IsAnomaly.astype(bool)
    actual = out.IsSyntheticInjectedAnomaly.astype(bool)
    tp=int((predicted & actual).sum()); fp=int((predicted & ~actual).sum())
    fn=int((~predicted & actual).sum()); tn=int((~predicted & ~actual).sum())
    precision=tp/(tp+fp) if tp+fp else None
    recall=tp/(tp+fn) if tp+fn else None
    f1=2*precision*recall/(precision+recall) if precision is not None and recall is not None and precision+recall else None
    metadata={'train_lines':int(train.sum()),'excluded_labeled_training_lines':int(((dates<=split)&labeled).sum()),
            'evaluated_lines':int(evaluation.sum()),'training_cutoff':str(split.date()),
            'flagged_lines':int(predicted.sum()),'synthetic_positive_lines':int(actual.sum()),
            'true_positives':tp,'false_positives':fp,'false_negatives':fn,'true_negatives':tn,
            'precision':precision,'recall':recall,'f1':f1,
            'limitations':['Precision, recall and F1 apply only to deterministic injected high-quantity anomalies, not real-world fraud or every business anomaly.',
                           'Unlabeled unusual records are counted as negatives, so measured precision can understate useful review flags.',
                           'Large legitimate orders can be flagged; human review is required.']}
    return out.sort_values('AnomalyScore'),metadata,{'model':model,'scaler':scaler,'features':cols}
