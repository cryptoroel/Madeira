import sys

sys.path.append('/home/rheremans/Repos/CryptoMadeira/source')

from os import path
import json
import time
from datetime import datetime
from automatic_trading.tools import create_debug_observing_files, state_machine_auto_trade
from api.binance_api import make_wallet_info_request, make_direct_order


def write_buy_sell_summary_file(coin_dict, action_string, walletInfoBefore, walletInfoAfter):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    coins = coin_dict['static_transaction_amount']

    with open(path.join(coin_dict['out_dir'], f"reality_{coin_dict['filename_out']}.log"), 'a') as f:
        if action_string == 'sell':
            print(f"{now}, USDT after SELL action: {float(walletInfoAfter['free']):.2f}  " 
                  f"-->  AT: {(float(walletInfoAfter['free']) - float(walletInfoBefore['free'])) / coins:.5f}", file=f)
        elif action_string == 'buy':
            print(f"{now}, USDT after BUY  action: {float(walletInfoAfter['free']):.2f}  "
                  f"-->  AT: {(float(walletInfoBefore['free']) - float(walletInfoAfter['free'])) / coins:.5f}", file=f)


if __name__ == "__main__":
    out_dir = path.join(path.dirname(path.abspath(__file__)), '..', 'outputs', 'automatic_trade')
    symbol = 'BTCUSDT'

    # Initial coin dictionary containing all the parameters needed for the optimal buy opportunity
    coin_dict_initial = {'out_dir': out_dir,  # path to output
                         'filename_out': f"auto_trade_auto_buy_{symbol}",
                         'symbol': symbol,  # e.g 'BTCUSDT'
                         'tolerance': 150,  # tolerance value to change the trend up <-> down expressed in USDT
                         'current_trend': -1,  # initial trend 1 means up trend, sell during next down trend
                         'max_buy_price': 26600.0,
                         'max_buy_price_reached': 0,  # Flag to see if the min_sell_price is reached (1) or not (0)
                         'manual_price_input': 0,  # Flag for testing (feeding the price with console inputs)
                         'print_precision': 5,  # number of digits after comma
                         'action_flag': 'IDLE',  # this flag will move between 'idle', 'buy' and 'sell'
                         'filled_flag': 0,  # this flag indicates if the one time sell has been performed or not
                         'static_transaction_amount': 0.025}  # the amount of coins during buy and sell strategy

    create_debug_observing_files(coin_dict_initial)
    coin_dict = state_machine_auto_trade(coin_dict_initial)

    if coin_dict['max_buy_price_reached'] and coin_dict['action_flag'] == 'buy' and coin_dict['filled_flag'] == 0:
        walletInfoBeforeBuy = make_wallet_info_request('USDT')
        #make_direct_order('BUY', coin_dict_initial['symbol'], coin_dict_initial['static_transaction_amount'])
        time.sleep(5)
        walletInfoAfterBuy = make_wallet_info_request('USDT')
        write_buy_sell_summary_file(coin_dict_initial, coin_dict['action_flag'], walletInfoBeforeBuy,
                                    walletInfoAfterBuy)

        coin_dict['filled_flag'] = 1
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        precision = coin_dict['print_precision']
        with open(path.join(coin_dict['out_dir'], coin_dict['filename_out'] + '.log'), 'a') as f:
            print(f"{now}:{coin_dict['action_flag']:>4} at {coin_dict['buy_price']:.{precision}f} ", file=f)
        with open(path.join(coin_dict['out_dir'], coin_dict['filename_out'] + '.json'), 'w') as outfile:
            json.dump(coin_dict, outfile)
