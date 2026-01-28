"""ETL script: load CSVs, validate, and upsert into relational DB (SQLite default).

Idempotent: deduplicates on (datetime,state) and (datetime,region).
Validation rules: no negative demand, missing data < 5% threshold.
"""
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
import os

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / 'data_ingestion'
DB_URL = os.getenv('PM_DB_URL', 'sqlite:///'+str(BASE / 'data.db'))


def validate_demand(df: pd.DataFrame):
    if (df['demand_mw'] < 0).any():
        raise ValueError('Negative demand found')
    missing_frac = df.isna().mean().max()
    if missing_frac > 0.05:
        raise ValueError(f'Too much missing data: {missing_frac:.2%}')


def validate_price(df: pd.DataFrame):
    if (df['price_rs_per_mwh'] < 0).any():
        raise ValueError('Negative price found')
    missing_frac = df.isna().mean().max()
    if missing_frac > 0.05:
        raise ValueError(f'Too much missing data: {missing_frac:.2%}')


def upsert_table(df: pd.DataFrame, table: str, key_cols):
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        # write to temp table then dedupe into main table
        temp = f'{table}_tmp'
        df.to_sql(temp, conn, if_exists='replace', index=False)
        # create main table if not exists
        cols = ','.join(df.columns)
        # simple upsert: delete duplicates in main that exist in temp then append
        join_cond = ' AND '.join([f"main.{c}=temp.{c}" for c in key_cols])
        conn.execute(text(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM {temp} WHERE 0=1"))
        conn.execute(text(f"DELETE FROM {table} WHERE EXISTS (SELECT 1 FROM {temp} temp WHERE {join_cond})"))
        conn.execute(text(f"INSERT INTO {table} SELECT * FROM {temp}"))
        conn.execute(text(f"DROP TABLE {temp}"))


def run():
    df_d = pd.read_csv(DATA_DIR / 'power_demand_hourly_mock.csv', parse_dates=['datetime'])
    df_p = pd.read_csv(DATA_DIR / 'power_price_dam_mock.csv', parse_dates=['datetime'])

    validate_demand(df_d)
    validate_price(df_p)

    upsert_table(df_d, 'power_demand_hourly', ['datetime', 'state'])
    upsert_table(df_p, 'power_price_dam', ['datetime', 'region'])
    print('ETL completed: data loaded into DB at', DB_URL)


if __name__ == '__main__':
    run()
