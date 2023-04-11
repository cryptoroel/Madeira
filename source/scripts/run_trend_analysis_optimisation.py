import os
from collections import deque
import numpy as np
from datetime import date, datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from api.binance_api import get_binance_time
from automatic_trading.tools import analyse_buy_sell_strategy, check_trend, make_swing_trade_plot
from api.aggregations import extract_binance_data




def get_data_from_binance(trade_config):
    symbol = trade_config['coin'].replace('/','')
    interval = trade_config['interval']
    last_x_days = trade_config['last_x_days']
    my_df = extract_binance_data(symbol, interval, last_x_days)

    my_df = my_df.loc[:,['close']]
    my_df.rename(columns={"close": "price"}, inplace=True)
    return my_df

def add_trend_to_df(my_df, tolerance):
    a = deque(list(my_df['price'].values))
    total_trend = []
    check_trend(a[0], a[0], a, 0, total_trend,tolerance=tolerance)
    my_df['trend'] = total_trend
    return my_df

def find_best_tolerance_value(trade_config, df):
    fig = True
    # find the min and max value of the coin price in the last x days
    price = df['price']
    v = [x for x in price.values]
    t = [get_binance_time(x) for x in price.index]
    time_frame_under_study = round((t[-1]-t[0])/(1000*3600*24))
    coin_min_max_range = max(v) - min(v)
    print('with Min: {:.3f}, Max: {:.3f}, Range: {:.1f} on a timeframe of {}day(s)'.\
          format( min(v), max(v), coin_min_max_range, time_frame_under_study))
    tenth = coin_min_max_range/10.
    tousandth = coin_min_max_range/1000.
    nr_steps = 160

    grid_search = np.linspace(max(tenth-nr_steps/2*tousandth,0), min(tenth+nr_steps/2*tousandth,max(v)), nr_steps)
    balance_list = []
    for tol in grid_search:
        trade_config.update({'tolerance': tol})
        my_df = df.copy()
        df_price = add_trend_to_df(my_df, tol)
        balance, buy_sell_tpl = analyse_buy_sell_strategy(df_price)
        balance_list.append([tol,balance])

    title_txt = '{}: Range={:.2g}, with grid search \nfrom {:.2g}-{:.2g} in {} steps of {:.2g}'.\
        format(trade_config['coin'],coin_min_max_range,grid_search[0], grid_search[-1], nr_steps, grid_search[1]- grid_search[0])
    if fig:
        plt.figure(figsize=(12,6))
        x= [x[0] for x in balance_list]
        y= [x[1] for x in balance_list]
        plt.plot(x,y)
        plt.scatter(x[np.argmax(y)],max(y))
        plt.text(x[np.argmax(y)],max(y), 'Optima={:.3g}'.format(x[np.argmax(y)]))
        plt.hlines(0,grid_search[0], grid_search[-1])
        plt.grid()
        plt.title(title_txt)
        dir_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'outputs', 'trends')
        if not os.path.exists(dir_out):
            os.makedirs(dir_out)
        plt.savefig(os.path.join(dir_out, '{}_last-{}d_interval-{}_tolerance_optimisation_.png'.format(
            trade_config['coin'].replace('/',''),
            str(trade_config['last_x_days']),
            trade_config['interval'])))

    return x[np.argmax(y)]



if __name__ == "__main__":
    ''' Trend analysis  run on the offline data_collection data.'''
    trade_config ={'last_x_days': 4, 'coin': 'BTC/USDT', 'interval': '1m'}
    df = get_data_from_binance(trade_config)
    # getting the best tolerance value (grid search)
    best_tol = find_best_tolerance_value(trade_config, df)
    trade_config.update({'tolerance': best_tol})
    df = add_trend_to_df(df, best_tol)
    balance, buy_sell_tpl = analyse_buy_sell_strategy(df)
    print('\nAnalysis on the swing trade: {}'.format(balance))
    make_swing_trade_plot(df, balance, buy_sell_tpl, trade_config)