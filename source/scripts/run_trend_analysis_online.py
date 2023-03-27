import sys
sys.path.append('/home/rheremans/Repos/CryptoMadeira/source')

from os import path
from automatic_trading.tools import create_debug_observing_files, state_machine_auto_trade
if __name__ == "__main__":
    out_dir = path.join(path.dirname(path.abspath(__file__)), '..', 'outputs', 'automatic_trade')
    symbol = 'BTCUSDT'

    # Initial coin dictionary containing all the parameters needed for the automatic trading
    coin_dict2_initial = {'out_dir': out_dir,  # path to output
                      'filename_out': f"auto_trade_{symbol}.json",
                      # filname of the json containing state machine info
                      'symbol': symbol,  # e.g 'BTCUSDT'
                      'tolerance': 50,  # tolerance value to change the trend up <-> down expressed in USDT
                      'mav': 1,  # moving average taken over 5 measurements
                      'current_trend': 1,  # initial trend -1 means down trend, first buy during next up trend
                      # when autotrade starts with up trend, then add the field 'buy_price'
                      'buy_price': 0.45,'print_precision': 5,  # number of digits after comma
                      'action_flag': 'IDLE',  # this flag will move between 'idle', 'buy' and 'sell'
                      'static_transaction_amount': 0.025}  # the amount of coins during buy and sell strategy

    create_debug_observing_files(coin_dict2_initial)
    action = state_machine_auto_trade(coin_dict2_initial)