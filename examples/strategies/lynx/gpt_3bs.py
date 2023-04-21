# python
# 获取最近250根K线
import pandas as pd
from pytdx.hq import TdxHq_API
from pytdx.hq import *
from pytdx.params import *
from pytdx.reader import *
import pandas as pd

from czsc import Direction, NewBar, RawBar


# 使用PyTDx获取上证指数的最新250根日线数据
def read_ol():
    api = TdxHq_API()
    N = 250

    with api.connect('218.75.126.9', 7709):
        data = api.get_security_bars(TDXParams.KLINE_TYPE_DAILY, TDXParams.MARKET_SH, '000001', 0, N)
        df = api.to_df(data)
        # df = df.sort_values('datetime')
        # df = api.to_df(api.get_security_bars(TDXParams.KLINE_TYPE_DAILY, TDXParams.MARKET_SH, '000001', 0, N))
    return df

# 从文件读取日线
def read_file():
    path = r'D:\app_dev\tdx\vipdoc\sh\lday\sh000001.day'
    api = TdxDailyBarReader()
    df = api.get_df_by_file(path)[-250:]

    return df

def format_daily_tdx(df: pd.DataFrame, symbol: str):
    df.rename(columns={'volume': 'vol'}, inplace=True)
    df['symbol'] = symbol
    # 索引转换为trade_date列
    df['dt'] = df.index
    # 获取日期类型 datetime64,日期报错的原因是类型是int64
    print(df.index.dtype,df['dt'].dtype)
    df = df.reset_index(drop=True)
    df['id'] = range(len(df))
    df['freq'] = 'D'


    # debug date列改不了名的问题,经过index=None参数发现是index是日期,把索引转换为date列 或者取消索引
    # df.reset_index(drop=True)
    # df.to_csv('df1.csv',header=None,index=None)
    df.to_csv('df1.csv')
    # print(df)

    # 日期转换
    # df['dt'] = pd.to_datetime(df['dt'], unit='ns')
    # df['dt'] = pd.to_datetime(df['dt'], format='%Y-%m-%d',errors='coerce')
    df['dt'] = pd.to_datetime(df['dt'],  errors='coerce', unit='ns')

    # 按要求排序
    order = ['symbol', 'id', 'dt', 'freq', 'open', 'high', 'low', 'close','vol','amount']
    df = df[order]
    return df


def hb_kline(klines: pd.DataFrame) -> pd.DataFrame:
    new_klines = []
    i=0
    n = len(klines)
    while n >= 3 and i<n-2:
        k1 = klines.iloc[i]
        k2 = klines.iloc[i+1]
        k3 = klines.iloc[i+2]
        # 如果k1 k2不包含，把k1、k2加入新k数组，判断kk3是否应该合并
        if not is_contain(k1,k2):
            new_klines.append(k1)
            new_klines.append(k2)
            res=remove_include(k1,k2,k3)
            # 如何发生包含，合并后的k线加入新k数组;如果不合并，k3加入新数组
            if res[0]:
                new_klines.append(res[1])
            else:
                new_klines.append(k3)

        return new_klines

def is_contain(k1, k2):
    """
    判断两根K线k1和k2是否存在包含关系
    """
    # K线1的最高价大于K线2最高价且K线1最低价小于K线2最低价,则K线1包含K线2
    if k1['high'] > k2['high'] and k1['low'] < k2['low']:
        return True

    # K线1的最高价小于K线2最高价，且K线1最低价大于K线2最低价,则K线2包含K线1
    elif k1['high'] < k2['high'] and k1['low'] > k2['low']:
        return True
    else:
        return False
def remove_include(k1: NewBar, k2: NewBar, k3: RawBar):
    """去除包含关系：输入三根k线，其中k1和k2为没有包含关系的K线，k3为原始K线"""
    if k1.high < k2.high:
        direction = Direction.Up
    elif k1.high > k2.high:
        direction = Direction.Down
    else:
        k4 = NewBar(symbol=k3.symbol, id=k3.id, freq=k3.freq, dt=k3.dt, open=k3.open,
                    close=k3.close, high=k3.high, low=k3.low, vol=k3.vol, elements=[k3])
        return False, k4

    # 判断 k2 和 k3 之间是否存在包含关系，有则处理
    if (k2.high <= k3.high and k2.low >= k3.low) or (k2.high >= k3.high and k2.low <= k3.low):
        if direction == Direction.Up:
            high = max(k2.high, k3.high)
            low = max(k2.low, k3.low)
            dt = k2.dt if k2.high > k3.high else k3.dt
        elif direction == Direction.Down:
            high = min(k2.high, k3.high)
            low = min(k2.low, k3.low)
            dt = k2.dt if k2.low < k3.low else k3.dt
        else:
            raise ValueError

        if k3.open > k3.close:
            open_ = high
            close = low
        else:
            open_ = low
            close = high
        vol = k2.vol + k3.vol
        # 这里有一个隐藏Bug，len(k2.elements) 在一些及其特殊的场景下会有超大的数量，具体问题还没找到；
        # 临时解决方案是直接限定len(k2.elements)<=100
        elements = [x for x in k2.elements[:100] if x.dt != k3.dt] + [k3]
        k4 = NewBar(symbol=k3.symbol, id=k2.id, freq=k2.freq, dt=dt, open=open_,
                    close=close, high=high, low=low, vol=vol, elements=elements)
        return True, k4
    else:
        k4 = NewBar(symbol=k3.symbol, id=k3.id, freq=k3.freq, dt=k3.dt, open=k3.open,
                    close=k3.close, high=k3.high, low=k3.low, vol=k3.vol, elements=[k3])
        return False, k4


# 初始化存储分型的fx数组
def fx():
    fx = []

    # 遍历最近249根K线(从第2根开始)
    for i in range(2, len(df)-1):
        # 获取当前K线、前一根K线和后一根K线的最高价和最低价
        pre = df.iloc[i-1]
        curr = df.iloc[i]
        aft = df.iloc[i+1]

        # current_high = data.loc[i, 'high']
        # current_low = data.loc[i, 'low']
        # pre_high = data.loc[i - 1, 'high']
        # pre_low = data.loc[i - 1, 'low']
        # aft_high = data.loc[i + 1, 'high']
        # aft_low = data.loc[i + 1, 'low']

        # 判断当前K线是否为顶分型或底分型,如果是则添加到fx数组
        # if current_high > pre_high and current_high > aft_high:
        #     fx.append([1,i])  # 顶分型
        # elif current_low < pre_low and current_low < aft_low:
        #     fx.append([0,i])  # 底分型
        # if max(curr)

        print[curr]
    # 输出fx数组
    print(fx)



# df = read_ol()
df = read_file()
print(df.index.dtype)
df = format_daily_tdx(df,'000001.SH')

pd.set_option('display.max_columns',None)
# print(df[:10])
# print(df[240:])
print(df)

dfn = hb_kline(df)
print(dfn)