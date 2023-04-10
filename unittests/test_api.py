import unittest
from api.binance_api import get_actual_price, get_binance_time, get_clock_difference_local_vs_binance, get_human_time, \
    get_all_open_binance_orders, get_klines, make_wallet_info_request, make_limit_order, delete_limit_order,\
    make_direct_order


class MyTestCase(unittest.TestCase):


    def test_get_actual_price(self) -> None:
        price_dict = get_actual_price('BTC/USDT')
        self.assertTrue('symbol' in price_dict)
        self.assertTrue('price' in price_dict)

    def test_get_all_open_binance_orders(self) -> None:
        orders = get_all_open_binance_orders()
        if orders:
            nr_orders = len(orders)
        else:
            nr_orders = 0
        self.assertTrue(nr_orders >= 0)

    def get_binance_time(self) -> None:
        time = get_binance_time('2023-03-23 18:00:21')
        self.assertTrue(time == 1679594421000)

    def test_get_clock_difference_local_vs_remote(self) -> None:
        delta_time_ms = get_clock_difference_local_vs_binance()
        # difference between my local datetime and the datetime on binance server should be less than 1000 ms
        # In case of failing test try: https://feeding.cloud.geek.nz/posts/time-synchronization-with-ntp-and-systemd/
        self.assertTrue(delta_time_ms < 1000)

    def test_get_human_time(self) -> None:
        time = get_human_time(1679594421000)
        self.assertTrue(time == '2023-03-23 18:00:21')

    def test_get_klines(self) -> None:
        kls = get_klines('BTC/USDT', '1h')
        self.assertTrue(len(kls) > 3)

    def test_make_wallet_info_request(self) -> None:
        mwir = make_wallet_info_request('BTC')
        self.assertTrue(type(mwir) is dict)

    @unittest.skip("demonstrating skipping")
    def test_make_limit_order(self) -> str:
        req_make = make_limit_order('BUY', 'BTC/USDT', 0.02, 10000)
        req_delete = delete_limit_order('BTC/USDT', str(req_make['orderId']))
        self.assertTrue('orderId' in req_make)
        self.assertTrue('status' in req_delete)
        self.assertTrue(req_delete['status'] == 'CANCELED')

    @unittest.skip("demonstrating skipping")
    def test_make_direct_sell_order(self) -> str:
        req_make = make_direct_order('SELL', 'BTC/USDT', 0.02)
        self.assertTrue('orderId' in req_make)

if __name__ == '__main__':
    unittest.main()
