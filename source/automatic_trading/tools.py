import json
import os
import shutil
import numpy as np
from datetime import datetime
from api.binance_api import make_wallet_info_request, get_actual_price

def delete_debug_observing_files(coin_dict):
  out_dir = coin_dict['out_dir']
  if os.path.exists(out_dir):
    shutil.rmtree(out_dir)

def create_debug_observing_files(coin_dict):
  initial_usdt_in_wallet = make_wallet_info_request('USDT')
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
      print(f"Automatic trading on {coin_dict['symbol']}" \
            f"\n++++++++++++++++++++++++++++" \
            f"\nINITIAL USDT amount in Binance wallet: {initial_usdt_in_wallet['free']}\n", file=f)

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
