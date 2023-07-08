import concurrent
import random

from czsc_lib import *

def main():
    global DEBUG
    DEBUG = 2
    # 初始化 Tushare 数据缓存
    # dc = TsDataCache(data_path=r"D:\ts_data", refresh=True)
    # # 处理单个代码
    # #  512880.SH

    # single('000001.SH#I', 'D', 130)
    # single('000001.SH#I', '30min')
    # single('002624.SZ', 'D', 130)
    # single_3l(symbol)

    # rfresh_cache()
    get_one()
def rfresh_cache():
    dc = TsDataCache(data_path=r"D:\ts_data", refresh=True)
    # symbols = get_symbols(dc, 'index')
    symbols = get_symbols(dc, 'stock')
    freqs = ['15min', 'D']
    limit = None
    # print(symbols, freqs, limit)

    def execute_function(symbol, freq):
        delay = random.randint(1, 6)
        time.sleep(delay)
        get_bars(dc, symbol, freq, limit)

    # 创建一个线程池，最大线程数为10
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(execute_function, symbol, freq) for freq in freqs for symbol in symbols ]

        concurrent.futures.wait(futures)


def get_one():
    symbol, freq, limit = '000001.SH#I', '15min', None
    symbol = '001000.SZ#E'
    freq = 'D'

    bars = get_bars(dc, symbol, freq, limit)
    # bars = get_bars(dc, '000001.SH#I', '15min', limit)
    # bars = get_bars(dc, '000001.SH#I', 'D', limit)
    # print(bars[:2])


if __name__ == '__main__':
    main()
