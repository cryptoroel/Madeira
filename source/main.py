import os
from api.binance_api import get_actual_price, make_curl_request, makeWalletInfoRequest, get_all_open_binance_orders

if __name__ == '__main__':
    print(get_actual_price('BTCUSDT'))
    print(make_curl_request())
    #print(get_all_open_binance_orders())
