import itertools
import json
import os
import re
from collections import deque
import shutil
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from api.binance_api import make_wallet_info_request, get_actual_price


def delete_debug_observing_files(coin_dict):
  out_dir = coin_dict['out_dir']
  if os.path.exists(out_dir):
    shutil.rmtree(out_dir)


def create_debug_observing_files(coin_dict):
  initial_usdt_in_wallet = make_wallet_info_request('USDT')
  initial_btc_in_wallet = make_wallet_info_request('BTC')
  usdt_in_wallet = float(initial_usdt_in_wallet['free'])+float(initial_usdt_in_wallet['locked'])
  btc_in_wallet = float(initial_btc_in_wallet['free'])+float(initial_btc_in_wallet['locked'])
  btc_now_in_usdt = float(get_actual_price('BTCUSDT')['price'])
  out_dir = coin_dict['out_dir']

  if not os.path.exists(out_dir):
    os.makedirs(out_dir)

  # File written each time the state machine gets updated (currently 1 min interval see crontab) - Only for debug
  # purpose
  if not os.path.isfile(os.path.join(out_dir, coin_dict['filename_out']+'.log')):
    with open(os.path.join(out_dir, coin_dict['filename_out']+'.log'), 'w') as f:
      print(f"Automatic trading on {coin_dict['symbol']}.log" \
            f"\n++++++++++++++++++++++++++++", file=f)

  # File written with only the Buy-Sell information at effective buy-sell time  (the real stuff)
  if not os.path.isfile(os.path.join(out_dir, f"reality_{coin_dict['filename_out']}.log")):
    with open(os.path.join(out_dir, f"reality_{coin_dict['filename_out']}.log"), 'w') as f:
      print(f"Automatic trading on {coin_dict['symbol']}"
            f"\n++++++++++++++++++++++++++++"
            f"\nINITIAL USDT amount in Binance wallet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            f"\nFREE USDT: {initial_usdt_in_wallet['free']}"
            f"\nLOCKED USDT: {initial_usdt_in_wallet['locked']}"
            f"\nTOTAL USDT: {usdt_in_wallet}"
            f"\nINITIAL BTC amount in Binance wallet:" 
            f"\n BTC price at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {btc_now_in_usdt} USD"
            f"\nFREE BTC: {initial_btc_in_wallet['free']}"
            f"\nLOCKED BTC: {initial_btc_in_wallet['locked']}"
            f"\nTOTAL BTC: {float(initial_btc_in_wallet['free'])+float(initial_btc_in_wallet['locked'])}"
            f"\nTOTAL BTC in USDT (now): {btc_in_wallet*btc_now_in_usdt}"
            f"\n\nTOTAL USDT at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} is {btc_in_wallet*btc_now_in_usdt+usdt_in_wallet}", file=f)


def update_trend(v_min, v_max, v, trend, tolerance):
  if trend == 0:
    if (v - v_min) > tolerance:
      trend = 1
      v_min = v
      v_max = v
    elif (v - v_max) < -tolerance:
      trend = -1
      v_min = v
      v_max = v
    else:
      trend = 0
      if v < v_min:
        v_min = v
      elif v > v_max:
        v_max = v
  elif trend < 0:
    if (v - v_min) < 0:
      trend = -1
      v_min = v
    elif (v - v_min) < tolerance:
      trend = -1
      if v > v_max:
        v_max = v
    else:
      trend = +1
      v_min = v
      v_max = v
  # trend > 0 (up trend)
  else:
    if (v - v_max) > 0:
      trend = 1
      v_max = v
    elif (v_max - v) < tolerance:
      trend = 1
    else:
      trend = -1
      v_min = v
      v_max = v
  return v_min, v_max, trend


def update_my_v_stack(v_stack, v):
  """ Removes the first element of the list and adds the value v at the end of the remaining list"""
  len_v_stack = len(v_stack)
  v_stack.pop(0)
  v_stack.append(v)
  assert len(v_stack) == len_v_stack
  return v_stack


def state_machine_auto_trade_init(coin_dict):
  now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  auto_trade_file = os.path.join(coin_dict['out_dir'], coin_dict['filename_out']+'.json')
  # Goes through this part of the code when auto_trade_file is not existing (done only once at begin)

  request = get_actual_price(coin_dict['symbol'])
  actual_price = float(request['price'])

  # When no intial trend is given then the current_trend flag is put to 0 (i.e. no trend detected so far)
  if 'current_trend' in coin_dict:
    if coin_dict['current_trend'] == 1:
      coin_dict['buy_price'] = actual_price
  else:
    coin_dict['current_trend'] = 0

  # When no moving average is chosen, it means that the moving average window is equal to 1
  if not 'mav' in coin_dict:
    coin_dict['mav'] = 1

  usdt_request = make_wallet_info_request('USDT')

  # check if the amount of second coin that is free is enough to buy the requested first coin
  if not 'training_file' in coin_dict:
    if float(usdt_request['free']) < actual_price * coin_dict['static_transaction_amount']:
      print(f"Not enough USDT to buy {coin_dict['static_transaction_amount']} {coin_dict['symbol']}")

  coin_dict['usdt_at_start'] = float(usdt_request['free'])

  # v-stack is created with the number of moving averages
  coin_dict['v_stack'] = [actual_price] * coin_dict['mav']
  # current price is set to the mean over the numbers of values in the v_stack (i.e. Moving Average)
  current_ma_price = np.mean(coin_dict['v_stack'])
  coin_dict['v_min'] = current_ma_price
  coin_dict['v_max'] = current_ma_price
  with open(auto_trade_file, 'w') as outfile:
    json.dump(coin_dict, outfile)

  # writing the auto_trade.log file containing the result of the state machine updated each 1 min in cron job defined
  precision = coin_dict['print_precision']
  with open(os.path.join(coin_dict['out_dir'], coin_dict['filename_out']+'.log'), 'a') as f:
    print(coin_dict, file=f)
    print(f"{now}, "
          f"Price={actual_price:.{precision}f}, "
          #f"MA{coin_dict['mav']}Price={current_ma_price:.{precision}f}, "
          f"v_min={current_ma_price:.{precision}f}, "
          f"v_max={current_ma_price:.{precision}f}, "
          f"trend={coin_dict['current_trend']}",
          file=f)
  return coin_dict


def state_machine_auto_trade_update(coin_dict):
  now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  auto_trade_file = os.path.join(coin_dict['out_dir'], coin_dict['filename_out']+'.json')
  with open(auto_trade_file) as json_file:
    coin_dict = json.load(json_file)
  if coin_dict['manual_price_input'] == 1:
    actual_price = float(input('Price value: '))
  else:
    # getting the single actual price value from the exchange API and pop the left element of the v_stack and add new
    # price at the end of the stack
    request = get_actual_price(coin_dict['symbol'])
    actual_price = float(request['price'])
  coin_dict['v_stack'] = update_my_v_stack(coin_dict['v_stack'], actual_price)
  current_ma_price = np.mean(coin_dict['v_stack'])
  if 'min_sell_price' in coin_dict:
    if current_ma_price > coin_dict['min_sell_price']:
      coin_dict['min_sell_price_reached'] = 1
  if 'max_buy_price' in coin_dict:
    if current_ma_price < coin_dict['max_buy_price']:
      coin_dict['max_buy_price_reached'] = 1
  v_min_update, v_max_update, trend_update = update_trend(coin_dict['v_min'],
                                                          coin_dict['v_max'], current_ma_price,
                                                          coin_dict['current_trend'],
                                                          coin_dict['tolerance'])
  # update the action flag
  if (coin_dict['current_trend'] == 1) & (trend_update == -1):
    coin_dict['action_flag'] = 'sell'
    coin_dict['sell_price'] = current_ma_price
    if 'cumm_gain' in coin_dict:
      coin_dict['cumm_gain'] = coin_dict['cumm_gain'] + current_ma_price - coin_dict['buy_price']
    else:
      coin_dict['cumm_gain'] = current_ma_price - coin_dict['buy_price']
  elif (coin_dict['current_trend'] == -1) & (trend_update == 1):
    coin_dict['action_flag'] = 'buy'
    coin_dict['buy_price'] = current_ma_price
  else:
    coin_dict['action_flag'] = 'idle'

  # update coin_dict state machine
  coin_dict['v_min'] = v_min_update
  coin_dict['v_max'] = v_max_update
  coin_dict['current_trend'] = trend_update
  precision = coin_dict['print_precision']

  # save coin_dict state machine
  with open(auto_trade_file, 'w') as outfile:
    json.dump(coin_dict, outfile)

  # update the auto_trade.log file only in case the filled_flag=0
  if coin_dict['filled_flag'] == 0:
    with open(os.path.join(coin_dict['out_dir'], coin_dict['filename_out']+'.log'), 'a') as f:
      if 'sell' in coin_dict['filename_out']:
        print(f"{now}, "
            f"Price={actual_price:.{precision}f}, "
            #f"MA{coin_dict['mav']}Price={current_ma_price:.{precision}f}, "
            f"v_min={v_min_update:.{precision}f}, "
            f"v_max={v_max_update:.{precision}f}, "
            f"trend={trend_update:>2}, "
            f"action={coin_dict['action_flag']:>4}, "
            f"min_sell_price_reached={coin_dict['min_sell_price_reached']}, "
            f"v_stack={coin_dict['v_stack']}", file=f)
      elif 'buy' in coin_dict['filename_out']:
        print(f"{now}, "
            f"Price={actual_price:.{precision}f}, "
            #f"MA{coin_dict['mav']}Price={current_ma_price:.{precision}f}, "
            f"v_min={v_min_update:.{precision}f}, "
            f"v_max={v_max_update:.{precision}f}, "
            f"trend={trend_update:>2}, "
            f"action={coin_dict['action_flag']:>4}, "
            f"max_buy_price_reached={coin_dict['max_buy_price_reached']}, "
            f"v_stack={coin_dict['v_stack']}", file=f)
  return coin_dict


def state_machine_auto_trade(coin_dict):
  auto_trade_file = os.path.join(coin_dict['out_dir'], coin_dict['filename_out']+'.json')
  if not os.path.isfile(auto_trade_file):
    return state_machine_auto_trade_init(coin_dict)
  else:
    return state_machine_auto_trade_update(coin_dict)


def analyse_buy_sell_strategy(df):

  df['trend_diff'] = df['trend'].diff()
  # TODO check if 2 and -2 is in the trend_diff
  # TODO if not a feedback should be send to the user telling that the tolerance needs to be lowered

  buy_at = df.loc[df['trend_diff'] == 2]['price']
  if len(buy_at) == 0:
    balance = 0
    buy_sell_tpl = None
    return balance, buy_sell_tpl

  sell_at = df.loc[(df['trend_diff'] == -2) & (df.index > df.loc[df['trend_diff'] == 2].index[0])]['price']
  if len(buy_at) > len(sell_at):
    buy_sell_tpl = list(zip(buy_at[:-1].index, buy_at[:-1], sell_at.index, sell_at))
    balance = sum(sell_at.values - buy_at[:-1].values)
  else:
    buy_sell_tpl = list(zip(buy_at.index, buy_at, sell_at.index, sell_at))
    balance = sum(sell_at.values - buy_at.values)
  # for (buy_time, buy, sell_time, sell) in buy_sell_tpl:
  # print('Buy at {:.2f}, sell at {:.2f}, diff={:.2f}'.format(buy, sell, sell - buy))
  return balance, buy_sell_tpl


def read_training_data(file_name, **kwargs):
  f1 = lambda x: float(re.sub(r'^.*?=', '', str(x)))
  f2 = lambda x: re.sub(r'^.*?=', '', str(x))

  if 'auto_trade' in file_name:
    if 'coin_id' in kwargs:
      coin_id = kwargs['coin_id']

    df = pd.read_csv(file_name,
                     skiprows=3,
                     sep=',',
                     names=['Datetime', 'Price', 'MAPrice', 'v_min', 'v_max', 'trend', 'action'],
                     index_col='Datetime',
                     parse_dates=['Datetime'])
    df[['Price', 'MAPrice', 'v_min', 'v_max', 'trend']] = df[['Price', 'MAPrice', 'v_min', 'v_max', 'trend']].applymap(
      f1)
    df['action'] = df['action'].apply(f2)
    df.rename(columns={'Price': coin_id}, inplace=True)

  elif 'data_collection' in file_name:
    df = pd.read_csv(file_name, parse_dates=['Datetime'], index_col='Datetime')

  else:
    df = pd.DataFrame()

  return df


def get_grid_for_optimal_tolerance_search(df, coin_id):
  observed_coin_min = df[coin_id].min()
  observed_coin_max = df[coin_id].max()
  coin_min_max_range = observed_coin_max - observed_coin_min

  print('Coin: {} ({}) with Min: {:.3f}, Max: {:.3f}, Range: {:.1f}'.
        format(coin_id, get_symbol(coin_id)[0], observed_coin_min, observed_coin_max, coin_min_max_range))
  tenth = coin_min_max_range / 10.
  tousandth = coin_min_max_range / 1000.
  nr_steps = 160

  return np.linspace(max(tenth - nr_steps / 2 * tousandth, 0), min(tenth + nr_steps / 2 * tousandth, observed_coin_max),
                     nr_steps)


def get_optimal_tolerance_value(trade_config, method='offline'):
  """ trade_config contains the path and filename to the file that contains the recorded data (price of the coins in
  the portfolio per minute. Read the file in and add it to a dataframe. Do interpolation so that data are equaly spaced
  (frequency of 1 min) without gaps. Check if the desired coin under study is part of the dataframe. Perform the
  buy_and_sell_strategy and find the best tolerance value on the available data. Maybe do some cross validation (here
  the data can be split in 70%-30%)"""

  filename = trade_config['training_file']
  coin_id = trade_config['coin']
  df = read_training_data(filename, coin_id=coin_id)
  assert coin_id in df, 'Price data for {} is not available. Ending analysis'.format(coin_id)

  grid_search = get_grid_for_optimal_tolerance_search(df, coin_id)

  balance_list = []
  for tol in grid_search:
    trade_config.update({'tolerance': tol})
    df = get_df_for_single_tolerance(trade_config, method=method)
    balance, buy_sell_tpl = analyse_buy_sell_strategy(df)
    balance_list.append([tol, balance, buy_sell_tpl])
  return balance_list


def get_df_for_single_tolerance(trade_config, method='offline'):
  filename = trade_config['training_file']
  coin_id = trade_config['coin']
  df = read_training_data(filename, coin_id=coin_id)
  assert coin_id in df, 'Price data for {} is not available. Ending analysis'.format(coin_id)

  total_trend = []
  if method == 'offline':
    a = deque(list(df[coin_id].values))
    check_trend(a[0], a[0], a, 0, total_trend, tolerance=trade_config['tolerance'], i_loop=1)
  else:
    delete_debug_observing_files(trade_config)
    create_debug_observing_files(trade_config)
    state_machine_auto_trade_init(trade_config)
    for actual_price in df[coin_id].values:
      trade_config['v_stack'] = update_my_v_stack(trade_config['v_stack'], actual_price)
      current_ma_price = np.mean(trade_config['v_stack'])
      v_min_update, v_max_update, trend_update = update_trend(trade_config['v_min'],
                                                              trade_config['v_max'], current_ma_price,
                                                              trade_config['current_trend'],
                                                              trade_config['tolerance'])
      # update coin_dict state machine
      trade_config['v_min'] = v_min_update
      trade_config['v_max'] = v_max_update
      trade_config['current_trend'] = trend_update
      total_trend.append(trend_update)

  if total_trend:
    df['trend'] = total_trend
  else:
    df['trend'] = 0

  df['price'] = df[coin_id]

  return df


def make_swing_trade_plot(df, balance, buy_sell_tpl, trade_config):
  bins = 15
  dfdown = df.copy()
  dfup = df.copy()
  dfdown.loc[df['trend'] != -1, 'price'] = np.nan
  dfup.loc[df['trend'] != 1, 'price'] = np.nan

  plt.figure(figsize=(14, 8))
  plt.plot(df.index, df['price'], '--')
  if not dfdown.dropna().empty:
    plt.plot(dfdown.index, dfdown['price'], 'r')
  if not dfup.dropna().empty:
    plt.plot(dfup.index, dfup['price'], 'g')
  if buy_sell_tpl:
    for (buy_time, buy_price, sell_time, sell_price) in buy_sell_tpl:
      plt.scatter(buy_time, buy_price, marker='o', c='g')
      plt.scatter(sell_time, sell_price, marker='o', c='r')
  plt.grid()
  ax = plt.gca()
  plt.xticks(rotation=45)
  divider = make_axes_locatable(ax)
  axHisty = divider.append_axes("right", 1.2, pad=0.1, sharey=ax)
  axHisty.yaxis.set_tick_params(labelleft=False)
  axHisty.hist(df['price'].values, bins=bins, orientation='horizontal')
  axHisty.grid()

  coin = trade_config['coin']
  last_x_days = df.index[-1] - df.index[0]
  tolerance = trade_config['tolerance']
  if buy_sell_tpl:
    pct_gain = balance / buy_sell_tpl[0][1] * 100
  else:
    pct_gain = 0
  ax.set_title(f"{coin}, Time Range:{last_x_days},"\
      f"\ntolerance={tolerance:.5g}, Balance={balance:.5g}, Pct Gain={pct_gain:.1f}%")

  dir_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'outputs', 'trends')
  if not os.path.exists(dir_out):
    os.makedirs(dir_out)
  plt.savefig(os.path.join(dir_out, '{}_last-{}d_interval-{}_optimal_threshold_.png'.format(
    trade_config['coin'],
    str(trade_config['last_x_days']),
    trade_config['interval'])))

  plt.close()


def get_optimal_tolerance_from_balance_list(balance_list):
  tol = [x[0] for x in balance_list]
  balance = [x[1] for x in balance_list]
  buy_sell_tpl = [x[2] for x in balance_list]
  return tol[np.argmax(balance)], balance[np.argmax(balance)], buy_sell_tpl[np.argmax(balance)]


def make_trend_plot(balance_list, config, title_txt=''):
  plt.figure(figsize=(12, 6))
  x = [x[0] for x in balance_list]
  y = [x[1] for x in balance_list]
  plt.plot(x, y)
  plt.scatter(x[np.argmax(y)], max(y))
  plt.text(x[np.argmax(y)], max(y), f"Optima={x[np.argmax(y)]:.7f}")
  plt.grid()
  plt.title(title_txt)
  dir_out = os.path.dirname(config['training_file'])
  file_out = os.path.splitext(config['training_file'])[0].replace('auto_trade_', '')

  if not os.path.exists(dir_out):
    os.makedirs(dir_out)
  plt.savefig(os.path.join(dir_out, file_out))


def check_trend(v_min, v_max, v_list, trend, out_put, **kwargs):
  tol = kwargs['tolerance']
  #i_loop = kwargs['i_loop']

  v_full_list = v_list
  split_at = 500
  if len(v_full_list) > split_at:
    # split in n parts of 1000
    n_parts = int(len(v_full_list) / split_at)
    rest = np.mod(len(v_full_list), n_parts * split_at)

    for i in range(n_parts):
      from_id = i * split_at
      till_id = (i + 1) * split_at
      v_list = deque(itertools.islice(v_full_list, from_id, till_id))
      #v_min, v_max, trend = check_trend_on_subpart(v_min, v_max, v_list, trend, out_put, tolerance=tol, i_loop=i_loop)
      v_min, v_max, trend = check_trend_on_subpart(v_min, v_max, v_list, trend, out_put, tolerance=tol)

    # perform the remaining part
    if rest:
      from_id = (i + 1) * split_at
      till_id = len(v_full_list)
      v_list = deque(itertools.islice(v_full_list, from_id, till_id))
      #_, _, _ = check_trend_on_subpart(v_min, v_max, v_list, trend, out_put, tolerance=tol, i_loop=i_loop)
      _, _, _ = check_trend_on_subpart(v_min, v_max, v_list, trend, out_put, tolerance=tol)
  else:
    #check_trend_on_subpart(v_min, v_max, v_list, trend, out_put, tolerance=tol, i_loop=i_loop)
    check_trend_on_subpart(v_min, v_max, v_list, trend, out_put, tolerance=tol)


def check_trend_on_subpart(v_min, v_max, v_list, trend, out_put, tolerance=100, i_loop=1):
  if len(v_list) > 0:
    v = v_list.popleft()
    #print("i:{:4d}, {:.2f}, v-v_min condition {} >{} or v-v_max {} <-{}".format(
    #  i_loop, v, (v - v_min), tolerance, (v - v_max), tolerance))
    v_min, v_max, trend = update_trend(v_min, v_max, v, trend, tolerance)
    out_put.append(trend)
    # print("Iter: {:4d}: Trend={}".format(i_loop, trend))
    i_loop += 1
    return check_trend_on_subpart(v_min, v_max, v_list, trend, out_put, tolerance=tolerance, i_loop=i_loop)
  else:
    # print("End of the recursive process")
    return v_min, v_max, trend

