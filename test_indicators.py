import unittest
from paper_bot.indicators import ema, rsi, macd

class IndicatorsTests(unittest.TestCase):
    def test_constant_prices(self):
        prices = [10.0] * 50
        self.assertEqual(ema(prices, 9), 10)
        self.assertEqual(rsi(prices), 50)
        self.assertEqual(macd(prices), (0, 0, 0))
    def test_rsi_direction(self):
        self.assertEqual(rsi(list(range(30))), 100)
        self.assertEqual(rsi(list(range(30, 0, -1))), 0)
    def test_insufficient(self):
        with self.assertRaises(ValueError): macd([1, 2])

if __name__ == '__main__': unittest.main()
