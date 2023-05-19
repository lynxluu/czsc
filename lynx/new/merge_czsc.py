# import pip as ts
# from datetime import datetime
import datetime as dt
import traceback

import akshare as ak
import tushare as ts
import pandas as pd
# from czsc.traders.base import CzscSignals, BarGenerator
# from czsc.utils import freqs_sorted
from czsc.data import TsDataCache, get_symbols
from czsc.analyze import *
from czsc.data.ts import *
from czsc.enum import *
import requests
# from pandas import Timedelta

DEBUG = 0

def is_contained(k1, k2):
    if k1.high >= k2.high and k1.low <= k2.low or k1.high <= k2.high and k1.low >= k2.low:
        return k1.dt
    else:
        return None


def count_bars(bars) -> int:
    count = 0
    if len(bars) < 2:
        return 0
    for i in range(len(bars)-1):
        k1 = bars[i]
        k2 = bars[i+1]
        if is_contained(k1, k2) is not None:
            count += 1
    return count


def merge_bars(bars):
    # 1.若输入空列表或长度不大于2条，返回None
    if not bars or len(bars) <= 2:
        return []
    # elif len(bars) <= 2:
    #     return []

    n = len(bars)
    print('开始处理%d条k线：' % n, end=' ')

    # 2. 从bars头部寻找两条不包含的k线 加入结果列表n_bars
    n_bars = []
    for i, bar in enumerate(bars):
        if len(n_bars) < 2:
            # k1,k2 需要是 NewBar 现在都是RawBar 要转换，k3不变
            n_bars.append(NewBar(symbol=bar.symbol, id=bar.id, freq=bar.freq, dt=bar.dt,
                                       open=bar.open, close=bar.close,
                                       high=bar.high, low=bar.low, vol=bar.vol, elements=[bar]))
        else:
            k1, k2 = n_bars[-2:]
            if is_contained(k1,k2):
                n_bars.pop(0)

            k3 = bar

            # 如果k3时间比k2大，判断后合并
            if k3.dt > k2.dt:
                # print(i, len(n_bars),k1.dt,k2.dt,k3.dt)
                if DEBUG >= 3:
                    print(type(k1), type(k2), type(k3))
                has_include, k4 = remove_include(k1, k2, k3)
                if has_include:
                    # k2,k3包含，弹出k3,合并k4
                    n_bars.pop()
                    n_bars.append(k4)
                else:
                    # k2，k3不包含，直接合并k4
                    n_bars.append(k4)

        # 结果列表取最后两个
        if DEBUG >= 5:
            print(i, len(n_bars))

    print("合并后得到%d条k线" % len(n_bars))
    return n_bars


def test(dc, symbol, asset):
    symbol = symbol
    asset = asset
    freq = 'D'
    adj = 'qfq'

    today = dt.datetime.now()
    edt = today.strftime('%Y%m%d')
    sdt = '20200101'

    try:
        bars = dc.pro_bar(ts_code=symbol, asset=asset, adj=adj, freq=freq,
                          start_date=sdt, end_date=edt, raw_bar=True)

    except Exception as e:
        # 股票代码不正确，或其他原因导致bar 为空
        print("获取 %s k线数据失败：" % symbol)
        # tb = traceback.extract_tb(e.__traceback__)
        # traceback.print_exc()
        return None

    if DEBUG >= 3:
        print(bars[0])

    return merge_bars(bars)


def test_group(dc, symbols):
    res = []
    for each in symbols:
        symbol, asset = each.split('#')
        print(each, end=' ')
        res.append(test(dc, symbol, asset))
    return res


def main():
    global DEBUG
    print(DEBUG)
    DEBUG = 2
    # 初始化 Tushare 数据缓存
    dc = TsDataCache(data_path=r"D:\ts_data\share", refresh=True)

    # # 处理单个代码
    # # 000905.SH  000016.SH  512880.SH 688981.SH  000999.SZ  002624.SZ
    # symbol = '000001.SH'
    # res = test(dc, symbol)

    # # 处理批量代码
    symbols = get_symbols(dc, step='index')[:3]
    # symbols = ['600436.SH','600129.SH','688111.SH','688981.SH','000999.SZ','002624.SZ','300223.SZ','301308.SZ']
    res2 = test_group(dc, symbols)


if __name__ == '__main__':
    main()


