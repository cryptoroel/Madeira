import sys
sys.path.append('/home/rheremans/Repos/CryptoMadeira/source')

import os
import pandas as pd
from datetime import datetime
from api.binance_api import get_actual_price


if __name__ == "__main__":

  coins_to_get_price_from = ['BTCUSDT', 'ETHUSDT', 'MATICUSDT', 'MANAUSDT']
  data_collection_fname = '/home/rheremans/Repos/CryptoMadeira/source/outputs/data_collection/coins_pro_min_data'
  now = datetime.today()
  coin_price_dict = {}

  for coin_id in coins_to_get_price_from:
    actual_price = float(get_actual_price(coin_id)['price'])
    coin_price_dict.update({coin_id: [actual_price]})

  # read the csv file (of this month) when existing
  data_collection_fname = data_collection_fname + datetime.strftime(now, "_%Y_%m.csv")
  if os.path.exists(data_collection_fname):
    df_history = pd.read_csv(data_collection_fname, index_col="Datetime")

  # creating the single row dataframe with the current values for the coins
  df2 = pd.DataFrame.from_dict(coin_price_dict)
  df2['Datetime'] = datetime.strftime(now, "%Y-%m-%d %H:%M:%S")
  df2.set_index('Datetime', inplace=True)

  # append df2 to the df_history
  if os.path.exists(data_collection_fname):
    df_history = df_history.append(df2)
  else:
    if not os.path.exists(os.path.dirname(data_collection_fname)):
      os.makedirs(os.path.dirname(data_collection_fname))
    df_history = df2

  df_history.to_csv(data_collection_fname)