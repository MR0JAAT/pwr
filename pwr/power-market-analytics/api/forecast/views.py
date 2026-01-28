from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from pathlib import Path
import joblib
import pandas as pd
from datetime import timedelta
import numpy as np

BASE = Path(settings.BASE_DIR) if hasattr(settings, 'BASE_DIR') else Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE.parent / 'models'
DB_PATH = BASE.parent / 'data.db'


def latest_model(model_type):
    p = MODEL_DIR.glob(f'{model_type}_model_*.joblib')
    files = sorted(p)
    return files[-1] if files else None


class DemandForecast(APIView):
    def get(self, request):
        state = request.query_params.get('state')
        hours = int(request.query_params.get('hours', 24))
        if not state:
            return Response({'error': 'state is required'}, status=status.HTTP_400_BAD_REQUEST)
        model_file = latest_model('demand')
        if not model_file:
            return Response({'error': 'No demand model available'}, status=500)
        model = joblib.load(model_file)
        # simple naive forecast: use last available DB row per state
        df = pd.read_sql('power_demand_hourly', f'sqlite:///{DB_PATH}', parse_dates=['datetime'])
        dfs = df[df['state'] == state].sort_values('datetime')
        if dfs.empty:
            return Response({'error': 'No data for state'}, status=404)
        last = dfs.iloc[-1]
        forecasts = []
        lag_1 = last['demand_mw']
        lag_24 = dfs['demand_mw'].iloc[-24] if len(dfs) >= 24 else lag_1
        curr_time = pd.to_datetime(last['datetime'])
        for h in range(1, hours + 1):
            hour = (curr_time + timedelta(hours=h)).hour
            weekday = (curr_time + timedelta(hours=h)).weekday()
            temp = last.get('temperature', 25)
            X = np.array([[lag_1, lag_24, temp, hour, weekday]])
            pred = float(model.predict(X)[0])
            row = {'datetime': (curr_time + timedelta(hours=h)).isoformat(), 'demand_mw': pred}
            forecasts.append(row)
            lag_24 = lag_1
            lag_1 = pred
        return Response({'state': state, 'forecast': forecasts})


class PriceForecast(APIView):
    def get(self, request):
        region = request.query_params.get('region')
        hours = int(request.query_params.get('hours', 24))
        if not region:
            return Response({'error': 'region is required'}, status=status.HTTP_400_BAD_REQUEST)
        model_file = latest_model('price')
        if not model_file:
            return Response({'error': 'No price model available'}, status=500)
        model = joblib.load(model_file)
        df = pd.read_sql('power_price_dam', f'sqlite:///{DB_PATH}', parse_dates=['datetime'])
        dfr = df[df['region'] == region].sort_values('datetime')
        if dfr.empty:
            return Response({'error': 'No data for region'}, status=404)
        last = dfr.iloc[-1]
        curr_time = pd.to_datetime(last['datetime'])
        demand = last['demand_mw']
        renew = last['renewables_pct']
        forecasts = []
        for h in range(1, hours + 1):
            hour = (curr_time + timedelta(hours=h)).hour
            X = [[demand, renew, hour]]
            pred = float(model.predict(X)[0])
            forecasts.append({'datetime': (curr_time + timedelta(hours=h)).isoformat(), 'price_rs_per_mwh': pred})
            demand = pred * 0.001 + demand * 0.99
        return Response({'region': region, 'forecast': forecasts})


class ModelMetrics(APIView):
    def get(self, request):
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute('SELECT model_type, filename, trained_at, metric_name, metric_value FROM model_metrics ORDER BY trained_at DESC')
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]
        conn.close()
        return Response({'metrics': rows})
