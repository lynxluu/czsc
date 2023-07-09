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
    prefix = r'D:\ts_data\TS_CACHE\pro_bar_minutes'

    # symbols = get_symbols(dc, 'check')
    # symbols = get_symbols(dc, 'index')
    # symbols = get_symbols(dc, 'etfs')

    # symbols = get_symbols(dc, 'stock')
    # symbols = get_symbols(dc, 'stock')[::-1]

    # symbols = get_symbols(dc, 'train')
    symbols = get_symbols(dc, 'valid')

    freqs = ['15min', 'D']
    # freqs = ['D']
    adj = 'hfq' # 所有的回测数据都用的后复权,要声明, 否则默认是前复权
    limit = None
    # print(symbols, freqs, adj, limit)

    # 读取失败列表,再执行
    # try:
    #     symbols = pd.read_csv(prefix+r'\fail_symbols.csv')['symbol'].to_list()
    #     # freq = '15min'
    # except Exception as e:
    #     print(f'没有失败列表.')
    #     symbols = []

    fail_symbols = []   # 定义一个列表,保存没有获取到的symbol
    def execute_function(symbol, freq):
        delay = random.randint(3, 8)
        time.sleep(delay)
        res = get_bars(dc, symbol, freq, adj, limit)
        if not res: # 当没有获取到数据时,记录代码
            fail_symbols.append(symbol)

    # 创建一个线程池，最大线程数为10
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(execute_function, symbol, freq) for symbol in symbols for freq in freqs]

        concurrent.futures.wait(futures)

    # 收集失败列表
    if len(fail_symbols) > 0:
        df = pd.DataFrame(fail_symbols, columns=['symbol'])
        # df.set_index(['symbol','freq'], inplace=True,drop=False)
        df.to_csv(prefix + r'\fail_symbols.csv')
    else:
        print("所有数据都已更新成功,恭喜!")



def get_one():
    dc = TsDataCache(data_path=r"D:\ts_data", refresh=True, last_date='20230707')   #日线的last_date和分时线不一样,差15小时
    symbol, freq, adj, limit = '000001.SH#I', '15min', 'hqf', None

    # adj = 'hfq' # 所有的回测数据都用的后复权

    symbol = '000150.SZ#E'
    # freq = 'D'

    bars = get_bars(dc, symbol, freq, adj, limit)
    # get_bars(dc, '000999.SZ#E', freq, adj, limit)
    # get_bars(dc, '000998.SZ#E', freq, adj, limit)
    # get_bars(dc, '000997.SZ#E', freq, adj, limit)
    # bars = get_bars(dc, '000001.SH#I', '15min', limit)
    # bars = get_bars(dc, '000001.SH#I', 'D', limit)
    # print(bars[:2])


if __name__ == '__main__':
    main()
