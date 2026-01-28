"""Generate mock hourly demand and price CSVs for demo/testing."""
import pandas as pd
import numpy as np
from pathlib import Path
import datetime


OUT = Path(__file__).resolve().parent


def gen_demand(days=7, states=("HR", "DL", "MH")):
    now = pd.Timestamp.utcnow().floor('H')
    idx = pd.date_range(now - pd.Timedelta(days=days), now, freq='H')
    rows = []
    for ts in idx:
        for s in states:
            base = 3000 + (hash(s) % 1000)
            hour_factor = 1 + 0.3 * np.sin(2 * np.pi * ts.hour / 24)
            temp = 25 + 5 * np.sin(2 * np.pi * ts.dayofyear / 365) + np.random.randn()
            humidity = 50 + 10 * np.random.rand()
            demand = max(10, base * hour_factor + np.random.randn() * 100)
            rows.append({
                'datetime': ts,
                'state': s,
                'demand_mw': round(demand, 3),
                'temperature': round(temp, 2),
                'humidity': round(humidity, 2),
                'is_holiday': False,
            })
    return pd.DataFrame(rows)


def gen_price(days=7, regions=("NORTH", "SOUTH")):
    now = pd.Timestamp.utcnow().floor('H')
    idx = pd.date_range(now - pd.Timedelta(days=days), now, freq='H')
    rows = []
    for ts in idx:
        for r in regions:
            demand = 4000 + 500 * np.sin(2 * np.pi * ts.hour / 24) + np.random.randn() * 50
            renew_pct = max(0, min(100, 20 + 30 * np.sin(2 * np.pi * ts.hour / 24) + np.random.randn()*5))
            price = max(0, 3000 + 0.01 * demand - 5 * renew_pct + np.random.randn()*50)
            rows.append({
                'datetime': ts,
                'region': r,
                'price_rs_per_mwh': round(price, 3),
                'demand_mw': round(demand, 3),
                'renewables_pct': round(renew_pct, 2),
            })
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df_d = gen_demand(days=30)
    df_p = gen_price(days=30)
    df_d.to_csv(OUT / 'power_demand_hourly_mock.csv', index=False)
    df_p.to_csv(OUT / 'power_price_dam_mock.csv', index=False)
    print('Wrote mock CSVs to', OUT)


if __name__ == '__main__':
    main()
