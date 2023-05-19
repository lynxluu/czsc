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
    # 23-05-19: Index(['date', 'open', 'high', 'low', 'close', 'volume', 'outstanding_share', 'turnover']
    df['dt'] = df['date']
    df['vol'] = df['volume']
    df.index = pd.to_datetime(df['dt'])
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
        print(i,len(n_klines))
        k1, k2 = n_klines[-2], n_klines[-1]
        # 循环取待处理列表
        k3 = klines.iloc[i]
        k4 = None

        # 如果k2、k3包含，生成k4，弹出k2，合并k4
        if is_contained(k2, k3):
            # 上涨趋势
            if k1['high'] < k2['high']:
                k4 = {'open': k2['open'], 'close': k3['close'],
                      'high': max(k2['high'], k3['high']),
                      'low': max(k2['low'], k3['low']),
                      'vol': k2['vol'] + k3['vol'],
                      # 'amount': k2['amount'] + k3['amount'],
                      'dt': k3['dt'], 'symbol': k3['symbol']}
            # 下跌趋势
            elif k1['low'] > k2['low']:
                k4 = {'open': k2['open'], 'close': k3['close'],
                      'high': min(k2['high'], k3['high']),
                      'low': min(k2['low'], k3['low']),
                      'vol': k2['vol'] + k3['vol'],
                      # 'amount': k2['amount'] + k3['amount'],
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


def main():
    test1()

def test1():
    symbol = 'sh688981'
    klines = get_klines(symbol)
    merged_klines = merge_klines(klines)

    # 检查合并过的k线里 是否还有漏合并的k线
    print(len(merged_klines), count_klines(merged_klines))

if __name__ == '__main__':
    main()


