"""Weekly forecasting with rolling-origin backtests and a final unseen test."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def complete_weeks(sales, coverage_start, coverage_end):
    daily=sales.groupby('FullDate').NetSalesAmount.sum()
    daily.index=pd.to_datetime(daily.index)
    daily=daily.reindex(pd.date_range(coverage_start,coverage_end),fill_value=0)
    weekly=daily.resample('W-MON',label='left',closed='left').sum()
    counts=daily.resample('W-MON',label='left',closed='left').size()
    return weekly[counts==7].astype(float)


def features(history, stamp, cfg):
    week=stamp.isocalendar().week
    return [history[-lag] for lag in cfg['lags']] + [np.mean(history[-w:]) for w in cfg['rolling_windows']] + [np.sin(2*np.pi*week/52),np.cos(2*np.pi*week/52)]


def fit_model(name, series, cfg):
    if name in ('naive','moving_average'):
        return None
    if name=='exponential_smoothing':
        return ExponentialSmoothing(series.to_numpy(),trend='add',damped_trend=True,initialization_method='estimated').fit(optimized=True)
    if name not in ('random_forest','gradient_boosting'):
        raise ValueError(f'Unsupported forecasting model {name}')
    start=max(max(cfg['lags']),max(cfg['rolling_windows']))
    x=[features(series.iloc[:i].tolist(),series.index[i],cfg) for i in range(start,len(series))]
    y=series.iloc[start:].to_numpy()
    model=RandomForestRegressor(n_estimators=120,min_samples_leaf=4,random_state=cfg['random_state'],n_jobs=1) if name=='random_forest' else GradientBoostingRegressor(n_estimators=80,max_depth=2,min_samples_leaf=4,random_state=cfg['random_state'])
    return model.fit(x,y)


def predict(name, model, history, dates, cfg):
    if name=='exponential_smoothing':
        return np.maximum(model.forecast(len(dates)),0)
    values=list(map(float,history))
    out=[]
    last=values[-1]
    for stamp in dates:
        if name=='naive':
            value=last
        elif name=='moving_average':
            value=np.mean(values[-4:])
        else:
            value=model.predict([features(values,stamp,cfg)])[0]
        value=max(0,float(value)); out.append(value); values.append(value)
    return np.array(out)


def metrics(actual, predicted, training):
    actual=np.asarray(actual,dtype=float); predicted=np.asarray(predicted,dtype=float)
    error=actual-predicted
    scale=np.mean(np.abs(np.diff(np.asarray(training,dtype=float))))
    return {'MAE':float(np.abs(error).mean()),'RMSE':float(np.sqrt((error**2).mean())),
            'WAPE_percent':float(np.abs(error).sum()/np.abs(actual).sum()*100) if np.abs(actual).sum() else None,
            'MASE':float(np.abs(error).mean()/scale) if scale else None}


def rolling_origin_backtests(series, cfg):
    """Evaluate fixed-horizon forecasts on non-overlapping chronological folds."""
    horizon = int(cfg['test_size_weeks'])
    minimum_train = int(cfg.get('minimum_train_weeks', 104))
    available_folds = max(0, (len(series) - minimum_train) // horizon)
    folds = min(int(cfg.get('backtest_folds', 5)), available_folds)
    if folds < 1:
        raise ValueError(
            f'Insufficient complete weeks for rolling backtests: need at least '
            f'{minimum_train + horizon}, received {len(series)}'
        )
    origins = [len(series) - horizon * offset for offset in range(folds, 0, -1)]
    rows = []
    for fold, origin in enumerate(origins, start=1):
        train = series.iloc[:origin]
        validation = series.iloc[origin:origin + horizon]
        for name in cfg['models']:
            model = fit_model(name, train, cfg)
            predicted = predict(name, model, train.to_list(), validation.index, cfg)
            rows.append({
                'Fold': fold,
                'Model': name,
                'TrainWeeks': len(train),
                'TrainEnd': str(train.index[-1].date()),
                'ValidationStart': str(validation.index[0].date()),
                'ValidationEnd': str(validation.index[-1].date()),
                **metrics(validation, predicted, train),
            })
    detail = pd.DataFrame(rows)
    summary = detail.groupby('Model', as_index=False).agg(
        Folds=('Fold', 'nunique'),
        MAE_mean=('MAE', 'mean'), MAE_std=('MAE', 'std'),
        RMSE_mean=('RMSE', 'mean'), RMSE_std=('RMSE', 'std'),
        WAPE_percent_mean=('WAPE_percent', 'mean'),
        WAPE_percent_std=('WAPE_percent', 'std'),
        MASE_mean=('MASE', 'mean'), MASE_std=('MASE', 'std'),
    ).fillna(0.0)
    return detail, summary


def minimum_history_weeks(cfg):
    """Minimum complete weeks needed, including defaults for older configs."""
    return int(cfg.get('minimum_train_weeks', 104)) + 2 * int(
        cfg.get('test_size_weeks', 12)
    )


def forecast(series, cfg):
    horizon=int(cfg['test_size_weeks'])
    minimum_train=int(cfg.get('minimum_train_weeks',104))
    required_weeks = minimum_history_weeks(cfg)
    if len(series)<required_weeks:
        raise ValueError(
            f'Insufficient complete weeks: select at least {required_weeks} '
            'weeks for rolling backtests plus the final unseen test.'
        )
    development=series.iloc[:-horizon]; test=series.iloc[-horizon:]
    backtest_detail, backtest_summary = rolling_origin_backtests(development, cfg)
    selected = backtest_summary.sort_values(
        ['WAPE_percent_mean', 'MAE_mean', 'Model']
    ).iloc[0].Model
    test_rows=[]; predictions=[]
    for name in cfg['models']:
        model=fit_model(name,development,cfg)
        preds=predict(name,model,development.to_list(),test.index,cfg)
        test_rows.append({'Model':name,**metrics(test,preds,development)})
        predictions.extend({'WeekStart':str(d.date()),'Model':name,'Actual':float(y),'Predicted':float(p)} for d,y,p in zip(test.index,test,preds))
    final=fit_model(selected,series,cfg)
    future_dates=pd.date_range(series.index[-1]+pd.Timedelta(weeks=1),periods=cfg['forecast_horizon_weeks'],freq='7D')
    future=pd.DataFrame({'WeekStart':future_dates,'ForecastNetSales':predict(selected,final,series.to_list(),future_dates,cfg),'Model':selected})
    selected_backtest = backtest_summary[backtest_summary.Model == selected].iloc[0]
    metadata={'selected_model':selected,
              'selection_metric':'Lowest mean rolling-origin WAPE (MAE tie-break; final test unseen)',
              'backtest_folds':int(selected_backtest.Folds),
              'development_weeks':len(development),'test_weeks':len(test),
              'development_end':str(development.index[-1].date()),
              'test_start':str(test.index[0].date()),'test_end':str(test.index[-1].date()),
              'selected_model_backtest':{
                  key: float(selected_backtest[key]) for key in [
                      'MAE_mean','MAE_std','RMSE_mean','RMSE_std',
                      'WAPE_percent_mean','WAPE_percent_std','MASE_mean','MASE_std'
                  ]
              },
              'limitations':['Rolling-origin results estimate stability across historical synthetic periods; no causal or operational performance claim.',
                             'Synthetic growth-weighted dates and embedded promotions limit real-world forecasting value.',
                             'Recursive fixed-origin predictions use no observed fold/test target values.',
                             'Fiscal year and calendar year are treated as identical in this demonstration.']}
    bundle={'model':final,'model_name':selected,'config':cfg,'history':series,'metadata':metadata}
    return (metadata,backtest_summary,backtest_detail,pd.DataFrame(test_rows),
            pd.DataFrame(predictions),future,bundle)
