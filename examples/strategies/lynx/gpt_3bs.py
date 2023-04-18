# python
# 获取最近250根K线
import pandas as pd
from pytdx.hq import TdxHq_API
from pytdx.hq import *
from pytdx.params import *
from pytdx.reader import *
import pandas as pd


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
    klines = api.get_df_by_file(path)[-250:]

    return klines



# df = read_ol()
df = read_file()
# print(df)
# print(df[:10])
# print(df[240:])

# 初始化存储分型的fx数组
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