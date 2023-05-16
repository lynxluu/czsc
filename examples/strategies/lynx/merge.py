# import tushare as ts
import akshare as ak
import pandas as pd
import requests


# from pandas import Timedelta


def get_klines(symbol):
    # 设置tushare的token
    # ts.set_token('your_token')
    # pro = ts.pro_api()
    # df = pro.daily(ts_code=symbol, start_date='20220101', end_date='20230501')

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
        return k1['date']
    elif k1['high'] <= k2['high'] and k1['low'] >= k2['low']:
        return k1['date']
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
    # 若输入k线不大于2条，返回None
    n = len(klines)
    if n <= 2:
        return None

    n_klines = pd.DataFrame()
    # delta = Timedelta(1, unit='D')
    # for i, row in klines.iterrows():
    for i in range(len(klines)):
        # if len(n_klines) < 2:
        if len(n_klines) == 0:
            k1a, k2a = klines.iloc[i], klines.iloc[i+1]
            # k1a, k2a不包含，则加入；包含则下移
            if is_contained(k1a, k2a) is None:
                n_klines = pd.concat([n_klines, k1a.to_frame().T, k2a.to_frame().T])
                print(len(n_klines), n_klines)
                # continue
            else:
                continue


        k1, k2, k3, k4 = n_klines.iloc[-2], n_klines.iloc[-1], klines.iloc[i], None

        print(i,len(n_klines))
        # prt(k1), prt(k2), prt(k3), prt(k4)

        # 如果k2、k3包含，生成k4，弹出k2，写入k4
        if is_contained(k2, k3):
            if k1['high'] < k2['high']:
                k4 = pd.DataFrame({'open': k2['open'], 'close': k3['close'],
                                                  'high': max(k2['high'], k3['high']),
                                                  'low': max(k2['low'], k3['low']),
                                                  'volume': k2['volume'] + k3['volume'],
                                                  'turnover': k2['turnover'] + k3['turnover'],
                                                  'date': k3['date'], 'symbol': k3['symbol']},
                                                  # index=[i-delta])
                                                  index=k3.index)
            elif k1['low'] > k2['low']:
                k4 = pd.DataFrame({'open': k2['open'], 'close': k3['close'],
                                                  'high': min(k2['high'], k3['high']),
                                                  'low': min(k2['low'], k3['low']),
                                                  'volume': k2['volume'] + k3['volume'],
                                                  'turnover': k2['turnover'] + k3['turnover'],
                                                  'date': k3['date'], 'symbol': k3['symbol']},
                                                  # index=[i-delta])
                                                  index=k3.index)


            # print('进行合并：'), prt(k1), prt(k2), prt(k3), prt(k4)
            print("删除k2："), prt(k2)
            n_klines.drop(index=n_klines.index[-1], axis=0, inplace=True)
            # print('合并k4：'), prt(k4)
            print('合并k4：'),print(k4['high'])
            n_klines = pd.concat([n_klines, k4])

        else:
            # 如果k2，k3不包含，写入k3
            n_klines = pd.concat([n_klines, k3.to_frame().T])

    return n_klines

def merge_klines2(klines: pd.DataFrame) -> pd.DataFrame:
    # 若输入k线不大于2条，返回None
    n = len(klines)
    print('开始处理%d条k线：'%n)
    if n <= 2:
        return pd.DataFrame()

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


        k1, k2, k3, k4 = n_klines[-2], n_klines[-1], klines.iloc[i], None

        # print(i,len(n_klines))

        # 如果k2、k3包含，生成k4，弹出k2，合并k4
        if is_contained(k2, k3):
            if k1['high'] < k2['high']:
                k4 = {'open': k2['open'], 'close': k3['close'],
                      'high': max(k2['high'], k3['high']),
                      'low': max(k2['low'], k3['low']),
                      'volume': k2['volume'] + k3['volume'],
                      'turnover': k2['turnover'] + k3['turnover'],
                      'date': k3['date'], 'symbol': k3['symbol']}
            elif k1['low'] > k2['low']:
                k4 = {'open': k2['open'], 'close': k3['close'],
                      'high': min(k2['high'], k3['high']),
                      'low': min(k2['low'], k3['low']),
                      'volume': k2['volume'] + k3['volume'],
                      'turnover': k2['turnover'] + k3['turnover'],
                      'date': k3['date'], 'symbol': k3['symbol']}

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

if __name__ == '__main__':
    # symbol = '000001'
    symbol = 'sh688981'

    # klines = get_klines(symbol)[:8]
    klines = get_klines(symbol)

    merged_klines = merge_klines2(klines)
    # print(merged_klines[:5])

    # 检查合并过的k线里 是否还有漏合并的k线
    print(len(merged_klines), count_klines(merged_klines))

