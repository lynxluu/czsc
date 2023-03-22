import pandas as pd
# from pytdx.hq import TdxHq_API
# api = TdxHq_API()
# api.connect('119.147.212.81', 7709)
# data = api.get_security_bars(9, 0, '600328.SH', 0, 10)
# print(data
# https://www.cursor.so/ 生成代码

from pytdx.hq import TdxHq_API
from pytdx.params import TDXParams

from czsc.data import TsDataCache

api = TdxHq_API()
api.connect('218.75.126.9', 7709)

data = api.get_security_bars(TDXParams.KLINE_TYPE_15MIN, TDXParams.MARKET_SH, '600328', 0, 246)
# print(data[0])

pro_bar_minutes = []
for bar in data:
    bar_minutes = {
        'ts_code': '600328.SH',
        'trade_time': pd.to_datetime(bar['datetime'], format='%Y-%m-%d %H:%M:%S'),
        'high': bar['high'],
        'low': bar['low'],
        'close': bar['close'],
        'vol': bar['vol'],
        'amount': bar['amount']
    }
    pro_bar_minutes.append(bar_minutes)
print(pro_bar_minutes[0])


def checkdata2():
    sdt = '20181101'
    mdt = '20210101'
    edt = '20230315'
    symbol = '000001.SZ'
    dc = TsDataCache(data_path=r"D:\ts_data\share", refresh=False, sdt="20120101", edt="20221001")
    # 获取单个品种的基础周期K线
    bars = dc.pro_bar_minutes(ts_code=symbol, asset='E', freq='15min',
                               sdt=sdt, edt=edt, adj='qfq', raw_bar=True)
    print(bars[0])


checkdata2()