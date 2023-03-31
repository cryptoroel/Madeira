from datetime import datetime, timedelta
import pandas as pd

from api.binance_api import get_klines_df

def convert_interval(interval):
    interval_dict = {'1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30, '1h': 60, '4h': 240}
    return interval_dict[interval]

def extract_binance_data(symbol, interval, last_x_days):
    now = datetime.now().replace(second=0, microsecond=0)
    start_time = now - timedelta(days=last_x_days)
    appended_df = []
    lim = 1000

    while start_time < now and lim == 1000:
        df_to_add = get_klines_df(symbol, interval, start=start_time, limit=lim)
        appended_df.append(df_to_add)
        start_time += timedelta(minutes=(1000+1)*convert_interval(interval))
        lim = len(df_to_add)
    appended_df = pd.concat(appended_df)
    appended_df.index = pd.to_datetime(appended_df.index)
    appended_df.index.rename('datetime', inplace=True)
    return appended_df