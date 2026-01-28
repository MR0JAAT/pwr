"""Train demand and price models, save versioned joblib files, and store metrics in DB."""
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
import joblib
from sqlalchemy import create_engine, text
import os
import datetime

BASE = Path(__file__).resolve().parent.parent
DB_URL = os.getenv('PM_DB_URL', 'sqlite:///'+str(BASE / 'data.db'))
MODEL_DIR = BASE / 'models'
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_table(table):
    engine = create_engine(DB_URL)
    return pd.read_sql_table(table, engine, parse_dates=['datetime'])


def fe_demand(df):
    df = df.sort_values('datetime')
    df['hour'] = df['datetime'].dt.hour
    df['weekday'] = df['datetime'].dt.weekday
    df['lag_1'] = df.groupby('state')['demand_mw'].shift(1)
    df['lag_24'] = df.groupby('state')['demand_mw'].shift(24)
    df = df.dropna()
    X = df[['lag_1', 'lag_24', 'temperature', 'hour', 'weekday']]
    y = df['demand_mw']
    return X, y


def fe_price(df):
    df = df.sort_values('datetime')
    df['hour'] = df['datetime'].dt.hour
    df = df.dropna()
    X = df[['demand_mw', 'renewables_pct', 'hour']]
    y = df['price_rs_per_mwh']
    return X, y


def train_and_save():
    engine = create_engine(DB_URL)
    # Demand model
    try:
        df_d = load_table('power_demand_hourly')
    except Exception:
        print('No demand data found in DB; run ETL first.')
        return
    Xd, yd = fe_demand(df_d)
    split = int(0.8 * len(Xd))
    X_train, X_val = Xd.iloc[:split], Xd.iloc[split:]
    y_train, y_val = yd.iloc[:split], yd.iloc[split:]
    model_d = GradientBoostingRegressor()
    model_d.fit(X_train, y_train)
    pred_d = model_d.predict(X_val)
    mape = mean_absolute_percentage_error(y_val, pred_d)
    ts = datetime.datetime.utcnow().strftime('%Y%m%d%H%M')
    fn_d = MODEL_DIR / f'demand_model_{ts}.joblib'
    joblib.dump(model_d, fn_d)
    # Price model
    try:
        df_p = load_table('power_price_dam')
    except Exception:
        print('No price data found in DB; run ETL first.')
        return
    Xp, yp = fe_price(df_p)
    split = int(0.8 * len(Xp))
    X_train, X_val = Xp.iloc[:split], Xp.iloc[split:]
    y_train, y_val = yp.iloc[:split], yp.iloc[split:]
    model_p = RandomForestRegressor(n_estimators=50)
    model_p.fit(X_train, y_train)
    pred_p = model_p.predict(X_val)
    rmse = mean_squared_error(y_val, pred_p, squared=False)
    fn_p = MODEL_DIR / f'price_model_{ts}.joblib'
    joblib.dump(model_p, fn_p)

    # store metrics
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE IF NOT EXISTS model_metrics (model_type TEXT, filename TEXT, trained_at TEXT, metric_name TEXT, metric_value FLOAT)'))
        conn.execute(text("INSERT INTO model_metrics (model_type, filename, trained_at, metric_name, metric_value) VALUES ('demand', :fn, :ts, 'MAPE', :val)"), {'fn': str(fn_d.name), 'ts': ts, 'val': float(mape)})
        conn.execute(text("INSERT INTO model_metrics (model_type, filename, trained_at, metric_name, metric_value) VALUES ('price', :fn, :ts, 'RMSE', :val)"), {'fn': str(fn_p.name), 'ts': ts, 'val': float(rmse)})

    print('Trained and saved models:', fn_d, fn_p)


if __name__ == '__main__':
    train_and_save()
