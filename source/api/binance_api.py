import os
import json
import requests
import time
from datetime import datetime
import pandas as pd

from binance.client import Client

client = Client(os.environ['BINANCE_KEY'], os.environ['BINANCE_SECRET'])

def get_actual_price(symbol):
  """
  :param symbol: string reflecting the coin pair (e.g. 'BTCUSDT')
  :return: dictionary like {'symbol': 'BTCUSDT', 'price': '15665.06000000'}
  """
  queryS = "symbol=" + symbol
  url = 'https://api.binance.com/api/v3/ticker/price' + '?' + queryS
  return json.loads((requests.get(url)).text)

def get_clock_difference_local_vs_binance() -> float:
  delta_time_ms = abs(int(time.time() * 1000) - client.get_server_time()['serverTime'])
  return delta_time_ms

def get_all_open_binance_orders():
  orders = client.get_open_orders()
  if len(orders):
    assert len(orders) > 0
    df = []
    for order in orders:
      df.append([datetime.fromtimestamp(order['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                 'Binance',
                 order['symbol'],
                 order['type'],
                 order['side'],
                 float(order['price']),
                 float(order['origQty']),
                 float(order['origQty']) * float(order['price'])])

    return pd.DataFrame(df, columns=['Date', 'Exchange', 'Pair', 'Type', 'Side', 'Price', 'Amount', 'Total'])