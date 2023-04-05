import sys
sys.path.append('/home/rheremans/Repos/CryptoMadeira/source')

import time
from os import path
from automatic_trading.tools import create_debug_observing_files, state_machine_auto_trade, write_buy_sell_summary_file
from api.binance_api import make_wallet_info_request
if __name__ == "__main__":
    out_dir = path.join(path.dirname(path.abspath(__file__)), '..', 'outputs', 'automatic_trade')
    symbol = 'BTCUSDT'

    # Initial coin dictionary containing all the parameters needed for the automatic trading
    coin_dict_initial = {'out_dir': out_dir,  # path to output
                      'filename_out': f"03_auto_trade_{symbol}",
                      # filname of the json containing state machine info
                      'symbol': symbol,  # e.g 'BTCUSDT'
                      'tolerance': 18.6,  # tolerance value to change the trend up <-> down expressed in USDT
                      'mav': 1,  # moving average taken over 5 measurements
                      'current_trend': 0,  # initial trend -1 means down trend, first buy during next up trend
                      'manual_price_input': 0,
                      'print_precision': 2,  # number of digits after comma
                      'action_flag': 'IDLE',  # this flag will move between 'idle', 'buy' and 'sell'
                      'filled_flag': 0,
                      'static_transaction_amount': 0.025}  # the amount of coins during buy and sell strategy

    create_debug_observing_files(coin_dict_initial)
    coin_dict = state_machine_auto_trade(coin_dict_initial)

    if coin_dict['action_flag'] == 'buy':
        walletInfoBeforeBuy = make_wallet_info_request('USDT')
        #makeDirectOrder('BUY', symbol, coin_dict_initial['static_transaction_amount'])
        time.sleep(5)
        walletInfoAfterBuy = make_wallet_info_request('USDT')
        write_buy_sell_summary_file(coin_dict, walletInfoBeforeBuy, walletInfoAfterBuy)
    elif coin_dict['action_flag'] == 'sell':
        walletInfoBeforeBuy = make_wallet_info_request('USDT')
        #makeDirectOrder('SELL', symbol, coin_dict_initial['static_transaction_amount'])
        time.sleep(5)
        walletInfoAfterBuy = make_wallet_info_request('USDT')
        write_buy_sell_summary_file(coin_dict, walletInfoBeforeBuy, walletInfoAfterBuy)