import sys
sys.path.append('/home/rheremans/Repos/CryptoMadeira/source')

from os import path
import json
from automatic_trading.tools import create_debug_observing_files, state_machine_auto_trade
if __name__ == "__main__":
    out_dir = path.join(path.dirname(path.abspath(__file__)), '..', 'outputs', 'automatic_trade')
    symbol = 'BTCUSDT'

    # Initial coin dictionary containing all the parameters needed for the optimal sell opportunity
    coin_dict_initial = {'out_dir': out_dir,  # path to output
                         'filename_out': f"auto_trade_auto_sell_{symbol}.json",
                         'symbol': symbol,  # e.g 'BTCUSDT'
                         'tolerance': 50,  # tolerance value to change the trend up <-> down expressed in USDT
                         'current_trend': 1,  # initial trend 1 means up trend, sell during next down trend
                         'min_sell_price': 27700.0,
                         'min_sell_price_reached': 0,   # Flag to see if the min_sell_price is reached (1) or not (0)
                         'manual_price_input': 1,
                         'print_precision': 5,  # number of digits after comma
                         'action_flag': 'IDLE',  # this flag will move between 'idle', 'buy' and 'sell'
                         'filled_flag': 0,  # this flag indicates if the one time sell has been performed or not
                         'static_transaction_amount': 0.025}  # the amount of coins during buy and sell strategy


    create_debug_observing_files(coin_dict_initial)
    coin_dict = state_machine_auto_trade(coin_dict_initial)
    if coin_dict["min_sell_price_reached"] and coin_dict["action_flag"] == "sell" and coin_dict["filled_flag"] == 0:
        coin_dict["filled_flag"] = 1
        print("Min Selling price asked for was {}".format(coin_dict["min_sell_price"]))
        print("Executed at an Optimized selling price of {}".format(coin_dict["sell_price"]))
        with open(path.join(coin_dict['out_dir'], coin_dict['filename_out']), 'w') as outfile:
            json.dump(coin_dict, outfile)