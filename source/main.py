import os
from api.binance_api import get_actual_price

if __name__ == '__main__':
    print(get_actual_price('BTCUSDT'))
