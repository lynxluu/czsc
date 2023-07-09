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

    rfresh_cache()
    # get_one()
def rfresh_cache():
    dc = TsDataCache(data_path=r"D:\ts_data", refresh=True, last_date='20230707')   #日线的last_date和分时线不一样,差15小时, 统一为日线格式,对分时的进行调整
    # symbols = get_symbols(dc, 'index')
    symbols = get_symbols(dc, 'stock')[1000:2000]
    # symbols = get_symbols(dc, 'stock')[::-1]
    freqs = ['15min', 'D']
    # freqs = ['D']
    adj = 'hfq' # 所有的回测数据都用的后复权,要声明, 否则默认是前复权
    limit = None
    # print(symbols, freqs, adj, limit)

    def execute_function(symbol, freq):
        delay = random.randint(3, 8)
        time.sleep(delay)
        get_bars(dc, symbol, freq, adj, limit)

    # 创建一个线程池，最大线程数为10
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(execute_function, symbol, freq) for freq in freqs for symbol in symbols ]

        concurrent.futures.wait(futures)


def get_one():
    dc = TsDataCache(data_path=r"D:\ts_data", refresh=True, last_date='20230707')   #日线的last_date和分时线不一样,差15小时
    symbol, freq, limit = '000001.SH#I', '15min', None
    symbol = '000999.SZ#E'
    adj = 'hfq' # 所有的回测数据都用的后复权
    # freq = 'D'

    bars = get_bars(dc, symbol, freq, adj, limit)
    get_bars(dc, '000998.SZ#E', freq, adj, limit)
    get_bars(dc, '000997.SZ#E', freq, adj, limit)
    # bars = get_bars(dc, '000001.SH#I', '15min', limit)
    # bars = get_bars(dc, '000001.SH#I', 'D', limit)
    # print(bars[:2])


if __name__ == '__main__':
    main()
