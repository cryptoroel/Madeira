import os
import json
import hmac
import hashlib
import requests
import time
from datetime import datetime
import pandas as pd
from binance.client import Client
api_key_ro = os.environ['BINANCE_READONLY_KEY']
api_secret_ro = os.environ['BINANCE_READONLY_SECRET']
api_key_spot = os.environ['BINANCE_SPOT_KEY']
api_secret_spot = os.environ['BINANCE_SPOT_SECRET']
client = Client(api_key_spot, api_secret_spot)
"""
Documentation for the Public Rest Api For Binance (2023-03-13)
https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#public-rest-api-for-binance-2023-03-13
"""

def get_actual_price(symbol):
  """
  :param symbol: string reflecting the coin pair (e.g. 'BTCUSDT')
  :usage: get_actual_price('BTCUSDT')
  :return: dictionary like {'symbol': 'BTCUSDT', 'price': '15665.06000000'}
  """
  queryS = "symbol=" + symbol
  url = 'https://api.binance.com/api/v3/ticker/price' + '?' + queryS
  return json.loads((requests.get(url)).text)

def get_all_open_binance_orders():
    """
    :return: list of dictionaries
                {'symbol': 'BTCUSDT',
                 'orderId': 20598624856,
                 'orderListId': -1,
                 'clientOrderId': 'web_147a675e173f4e37af677aff34e402f7',
                 'price': '27440.00000000',
                 'origQty': '0.04000000',
                 'executedQty': '0.00000000',
                 'cummulativeQuoteQty': '0.00000000',
                 'status': 'NEW',
                 'timeInForce': 'GTC',
                 'type': 'LIMIT',
                 'side': 'BUY',
                 'stopPrice': '0.00000000',
                 'icebergQty': '0.00000000',
                 'time': 1679795510310,
                 'updateTime': 1679795510310,
                 'isWorking': True,
                 'workingTime': 1679795510310,
                 'origQuoteOrderQty': '0.00000000',
                 'selfTradePreventionMode': 'NONE'},
    """
    return client.get_open_orders()

def get_binance_time(human_time):
    """
    :param human_time: str like '2023-03-23 18:00:21'
    :return: int (e.g. 1679594421000)
    :usage get_binance_time('2023-03-23 18:00:21')
    """
    return int(datetime.timestamp(pd.to_datetime(human_time))*1000)

def get_clock_difference_local_vs_binance() -> float:
  delta_time_ms = abs(int(time.time() * 1000) - client.get_server_time()['serverTime'])
  return delta_time_ms

def get_human_time(binance_time):
    """
    :param binance_time: int like 1679594421000
    :return:str (e.g. '2023-03-23 18:00:21')
    :usage get_human_time(1679594421000)
    """
    return datetime.fromtimestamp(binance_time / 1000).strftime('%Y-%m-%d %H:%M:%S')

def get_klines(symbol,interval, **kwargs):
  """
  :param    symbol: string reflecting the coin pair (e.g. 'BTCUSDT')
            interval: time length of one candle (e.g. '1h')
            optional:
                start: start time of klines (e.g. '2018-01-01 00:00:00')
  :return: list (e.g.[ [1499040000000,      // Kline open time
                        "0.01634790",       // Open price
                        "0.80000000",       // High price
                        "0.01575800",       // Low price
                        "0.01577100",       // Close price
                        "148976.11427815",  // Volume
                        1499644799999,      // Kline Close time
                        "2434.19055334",    // Quote asset volume
                        308,                // Number of trades
                        "1756.87402397",    // Taker buy base asset volume
                        "28.46694368",      // Taker buy quote asset volume
                        "0"                 // Unused field, ignore.
                        ] ]
  :usage: get_klines('BTCUSDT','1h')
          get_klines('BTCUSDT','1h',start='2023-01-01 00:00:00)
  """
  queryS = "symbol=" + symbol + "&interval=" + interval
  if 'start' in kwargs.keys():
    queryS = queryS + "&startTime=" + str(get_binance_time(kwargs['start']))

  url = 'https://api.binance.com/api/v3/klines'+'?'+queryS
  return json.loads((requests.get(url)).text)

def get_klines_df(symbol,interval):
    """
    :param    symbol: string reflecting the coin pair (e.g. 'BTCUSDT')
            interval: time length of one candle (e.g. '1h')
            optional:
                start: start time of klines (e.g. '2018-01-01 00:00:00')param symbol:
    :param interval:
    :return pandas DataFrame with following columns:
            ['open', 'high', 'low', 'close', 'volume', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol']
            index is human readable time string
    :usage: get_klines_df('BTCUSDT','1h')
            get_klines_df('BTCUSDT','1h',start='2023-01-01 00:00:00)
    """
    columns = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav',
               'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore']
    data = pd.DataFrame(get_klines(symbol, interval), columns=columns, dtype=float)
    data.index = [pd.to_datetime(x, unit='ms').strftime('%Y-%m-%d %H:%M:%S') for x in data.open_time]
    usecols = ['open', 'high', 'low', 'close', 'volume', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol']
    data = data[usecols]
    return data

def make_direct_order(side, symbol, quantity):
    """
    :param side: 'BUY' or 'SELL'
    :param symbol:  trading pair (e.g. 'BTCUSDT')
    :param quantity: amount of coins during buy sell strategy
    :return
    :usage makeOrder('BUY', 'BTCUSDT', 0.02)
    """
    timestamp = int(round(time.time() * 1000))
    queryS = "symbol=" + symbol + \
             "&side=" + side + \
             "&type=MARKET" + \
             "&quantity=" + str(quantity) + \
             "&timestamp=" + str(timestamp)
    m = hmac.new(api_secret_spot.encode('utf-8'), queryS.encode('utf-8'), hashlib.sha256)
    header = {'X-MBX-APIKEY': api_key_spot}
    url = 'https://api.binance.com/api/v3/order' + '?' + queryS + '&signature=' + m.hexdigest()
    return requests.post(url, headers=header, timeout=30, verify=True)

def make_limit_order(side, symbol, quantity, price):
    """
    :param side: 'BUY' or 'SELL'
    :param symbol:  trading pair (e.g. 'BTCUSDT')
    :param quantity: amount of coins during buy sell strategy
    :param price: limit price
    :return
    :usage make_limit_order('BUY', 'BTCUSDT', 0.02, 10000)
    """
    timestamp = int(round(time.time() * 1000))
    queryS = "symbol=" + symbol + \
           "&side=" + side + \
           "&type=LIMIT" + \
           "&timeInForce=GTC" + \
           "&quantity=" + str(quantity) + \
           "&price=" + str(price) + \
           "&timestamp=" + str(timestamp)
    m = hmac.new(api_secret_spot.encode('utf-8'), queryS.encode('utf-8'), hashlib.sha256)
    header = {'X-MBX-APIKEY': api_key_spot}
    url = 'https://api.binance.com/api/v3/order' + '?' + queryS + '&signature=' + m.hexdigest()
    return requests.post(url, headers=header, timeout=30, verify=True).json()

def delete_limit_order(symbol, orderId):
    """
    :param symbol:  trading pair (e.g. 'BTCUSDT')
    :param orderId:

    :return
    :usage delete_limit_order('BTCUSDT', 20604255324)
    """
    timestamp = int(round(time.time() * 1000))
    queryS = "symbol=" + symbol + \
             "&orderId=" + orderId + \
             "&timestamp=" + str(timestamp)
    m = hmac.new(api_secret_spot.encode('utf-8'), queryS.encode('utf-8'), hashlib.sha256)
    header = {'X-MBX-APIKEY': api_key_spot}
    url = 'https://api.binance.com/api/v3/order' + '?' + queryS + '&signature=' + m.hexdigest()
    return requests.delete(url, headers=header, timeout=30, verify=True).json()



def make_wallet_info_request(symbol):
  """
   :param symbol: coin (e.g. 'BTC')
   :return: dictionary like {'asset': 'USDT', 'free': '4778.48267688', 'locked': '0.00000000'}
   :usage: client.get_asset_balance('BTC')
   """
  return client.get_asset_balance(symbol)




