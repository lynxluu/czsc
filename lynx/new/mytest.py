import unittest
from mylib import *


class Test(unittest.TestCase):

    # @staticmethod
    def test_get_bar(self):
        df = pd.read_csv('code.csv')
        # df = df[:10]
        df = df[-5:]
        test_cases = []
        for index, row in df.iterrows():
            symbol = row['symbol']
            exp_cnt = 800
            test_cases.append((symbol, 1, exp_cnt))
            test_cases.append((symbol, 2, exp_cnt))
        for symbol, api, exp_cnt in test_cases:
            # print(symbol, api, exp_cnt)
            with self.subTest(symbol=symbol):
                self.assertEqual(len(get_bars_4l(symbol=symbol, api=api)), exp_cnt)


if __name__ == "__main__":
    unittest.main()