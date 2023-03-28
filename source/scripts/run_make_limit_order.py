import sys
sys.path.append('/home/rheremans/Repos/CryptoMadeira/source')

from api.binance_api import make_limit_order

if __name__ == "__main__":
    req_make = make_limit_order('BUY', 'BTCUSDT', 0.02, 10000)