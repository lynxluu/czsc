# import pip as ts
# from datetime import datetime
import datetime

import akshare as ak
import tushare as ts
import pandas as pd
# from czsc.traders.base import CzscSignals, BarGenerator
# from czsc.utils import freqs_sorted
from czsc.data import TsDataCache, get_symbols
from czsc.analyze import *
from czsc.enum import *
import requests


# from pandas import Timedelta


def get_klines(symbol):
    df = ak.stock_zh_a_daily(symbol=symbol, adjust='qfq', start_date='20220101', end_date='20230512')

    # 打印列名
    # print(df.columns)
    # 将日期转换为datetime格式，并设置为索引
    df.index = pd.to_datetime(df['date'])
    df = df.sort_index()
    df['symbol'] = symbol
    return df


# def is_contained(k1, k2):
#     return (k1['high'] >= k2['high'] and k1['low'] <= k2['low']) or \
#     (k1['high'] <= k2['high'] and k1['low'] >= k2['low'])
#

def is_contained(k1, k2):
    if k1['high'] >= k2['high'] and k1['low'] <= k2['low']:
        return k1['dt']
    elif k1['high'] <= k2['high'] and k1['low'] >= k2['low']:
        return k1['dt']
    else:
        return None



def count_klines(klines:pd.DataFrame) -> int:
    count = 0
    if len(klines) < 2:
        return 0
    for i in range(len(klines)-1):
        k1 = klines.iloc[i]
        k2 = klines.iloc[i+1]
        if is_contained(k1, k2) is not None:
            count += 1
            # print('待合并计数:',count),prt(k1),print('--'),prt(k2)
            # print(count, k1['date'], k1['high'], k1['low'], '--', k2['date'], k2['high'], k2['low'])

    return count

def  prt(kline):
    if kline is not None:
        print(kline['symbol'],kline['date'],kline['high'],kline['low'])


def merge_klines(klines: pd.DataFrame) -> pd.DataFrame:
    # 1.若输入k线不大于2条，返回None
    n = len(klines)
    print('开始处理%d条k线：'%n)
    if n <= 2:
        return pd.DataFrame()

    # 2. 从klines头部寻找两条不包含的k线 加入结果列表n_klines
    n_klines = []
    for i in range(len(klines)):
        if len(n_klines) == 0 and i < n:
            k1a, k2a = klines.iloc[i], klines.iloc[i+1]
            # k1a, k2a不包含，则加入；包含则下移
            if is_contained(k1a, k2a) is None:
                n_klines.append(k1a)
                n_klines.append(k2a)
            else:
                continue
        # 结果列表取最后两个
        k1, k2 = n_klines[-2], n_klines[-1]
        # 循环取待处理列表
        k3 = klines.iloc[i]
        k4 = None

        # print(i,len(n_klines))

        # 如果k2、k3包含，生成k4，弹出k2，合并k4
        if is_contained(k2, k3):
            # 上涨趋势
            if k1['high'] < k2['high']:
                k4 = {'open': k2['open'], 'close': k3['close'],
                      'high': max(k2['high'], k3['high']),
                      'low': max(k2['low'], k3['low']),
                      'vol': k2['vol'] + k3['vol'],
                      'amount': k2['amount'] + k3['amount'],
                      'dt': k3['dt'], 'symbol': k3['symbol']}
            # 下跌趋势
            elif k1['low'] > k2['low']:
                k4 = {'open': k2['open'], 'close': k3['close'],
                      'high': min(k2['high'], k3['high']),
                      'low': min(k2['low'], k3['low']),
                      'vol': k2['vol'] + k3['vol'],
                      'amount': k2['amount'] + k3['amount'],
                      'dt': k3['dt'], 'symbol': k3['symbol']}

            n_klines.pop()
            new_k = pd.DataFrame.from_dict(k4, orient='index').T.iloc[-1]
            n_klines.append(new_k)

        else:
            # 如果k2，k3不包含，合并k3
            n_klines.append(k3)

    res = pd.DataFrame(n_klines)
    print("合并后得到%d条k线"%len(n_klines))
    return res
    # return n_klines


def crt_newbar(row):
    # 从 row 中获取各个属性值
    symbol = row['symbol']
    id = row['id']
    dt = row['dt']
    freq = Freq(row['freq'])
    open = row['open']
    close = row['close']
    high = row['high']
    low = row['low']
    vol = row['vol']
    amount = row['amount']

    # 创建 NewBar 对象
    newbar = NewBar(symbol=symbol, id=id, dt=dt, freq=freq, open=open, close=close, high=high, low=low, vol=vol,
                    amount=amount, elements=[],cache=[])

    return newbar

def  prt3(kline):
    if kline is not None:
        print(kline.symbol,kline.dt,kline.high,kline.low)
def is_contained3(k1, k2):
    if k1.high >= k2.high and k1.low <= k2.low:
        return k1.dt
    elif k1.high <= k2.high and k1.low >= k2.low:
        return k1.dt
    else:
        return None
def count_klines3(klines) -> int:
    count = 0
    if len(klines) < 2:
        return 0
    for i in range(len(klines)-1):
        k1 = klines[i]
        k2 = klines[i+1]
        if is_contained3(k1, k2) is not None:
            count += 1
    return count

def merge_klines3(klines):
    # 1.df转列表，若输入k线不大于2条，返回None
    if not klines:
        return []

    newbars = klines.apply(crt_newbar, axis=1)
    n = len(newbars)
    print('开始处理%d条k线：'%n)
    if n <= 2:
        return []



    # 2. 从klines头部寻找两条不包含的k线 加入结果列表n_klines
    n_klines = []
    for i in range(len(klines)):
        if len(n_klines) == 0 and i < n:
            # k1a, k2a不包含，则加入
            k1a, k2a = newbars[i], newbars[i+1]
            if is_contained3(k1a, k2a) is None:
                n_klines.append(k1a)
                n_klines.append(k2a)


        # 结果列表取最后两个
        k1, k2 = n_klines[-2], n_klines[-1]
        # 循环取待处理列表
        k3 = newbars[i]

        # 如果k3时间比k2大，判断后合并
        if k3.dt > k2.dt:
            # print(i, len(n_klines),k1.dt,k2.dt,k3.dt)
            flag, k4 = remove_include(k1, k2, k3)
            if flag:
                n_klines.pop()
                n_klines.append(k4)
            else:
                # 如果k2，k3不包含，合并k3
                n_klines.append(k3)

            # if is_contained3(k2,k3):
            #     _, k4 = remove_include(k1, k2, k3)
            #     n_klines.pop()
            #     n_klines.append(k4)
            #     prt3(k2, k3)
            # else:
            #     n_klines.append(k3)

    # res = pd.DataFrame(n_klines)
    res = n_klines
    print("合并后得到%d条k线" % len(n_klines))
    return res

def main():
    # 初始化 Tushare 数据缓存
    dc = TsDataCache(data_path=r"D:\ts_data\share", refresh=True)
    symbols = get_symbols(dc, step='index')
    print(symbols)
    # symbol = '688981.SH'
    freq = 'D'
    asset = 'E'
    adj = 'qfq'

    today = datetime.datetime.now()
    edt = today.strftime('%Y%m%d')
    delta = datetime.timedelta(days=365*10)
    sdt = (today-delta).strftime('%Y%m%d')
    # sdt = '20200101'

    # df = None
    bars = []
    for symbol in symbols:
        symbol = symbol.split('#')[0]
        print(symbol, asset, adj, freq, sdt, edt)
        try:
            bars = dc.pro_bar(ts_code=symbol, asset=asset, adj=adj, freq=freq,
                                  start_date=sdt, end_date=edt, raw_bar=True)

            # bars = ts.pro_bar(ts_code=symbol, asset=asset, adj=adj, freq=freq,
            #                       start_date=sdt, end_date=edt)
            # 实际上dc.pro_bar已经取到最新的k线了，无需费心
            print(bars[0],bars[-1])
        except Exception as e:
            print(e)

        # df = pd.DataFrame(bars)
        # print(sdt, edt, len(bars))

        # merged_klines = merge_klines(df)
        merged_klines3 = merge_klines3(bars)

        # print(len(merged_klines), count_klines(merged_klines))

def test1():
    symbol = 'sh688981'
    klines = get_klines(symbol)
    merged_klines = merge_klines(klines)

    # 检查合并过的k线里 是否还有漏合并的k线
    print(len(merged_klines), count_klines(merged_klines))

if __name__ == '__main__':
    main()


