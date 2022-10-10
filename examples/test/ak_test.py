import akshare as ak
import czsc.data.ts_cache
from czsc.sensors.stocks import StocksDaySensor, TsDataCache
import pandas as pd
from czsc.data.ts import *
from czsc.data.ak import *
from czsc.sensors.stocks import StocksDaySensor, TsDataCache
# from czsc.sensors.stocks import *
def test_ak():
    # 东财历史行情数据
    # adjust=“” "qfq" “hfq” 对应不复权，前复权，后复权
    # df = ak.stock_zh_a_hist(symbol="000300", period="daily", start_date="20170301", end_date='20210907', adjust="qfq")

    # df = ak_pro_bar(ts_code='000001.SH', asset='E', adj='qfq', freq='D',
    #                                start_date='20210301', end_date='20210907')
    # print(df.head(2))

    df1 = ak_pro_bar(ts_code='000001.SH', asset='E', adj='qfq', freq='60min',
                     start_date='20220301', end_date='20220907')

    # df2 = ak_pro_bar(ts_code='000300', asset='I', adj='qfq', freq='D',
    #                                start_date='20210301', end_date='20210907')
    print(df1.head(2))

def test_tu():
    data_path = r"E:\usr\ts_data_czsc"
    dc = TsDataCache(data_path, sdt='2000-01-01', edt='2022-03-23', site='ak')
    df = dc.pro_bar(ts_code='000300', start_date='2000-01-01', end_date='2022-03-23', freq='D', adj='qfq')
    print(df.head(2))
    # dc.pro_bar(ts_code, start_date=None, end_date=None, freq='D', asset="E", adj='qfq', raw_bar=True):


def test_ak_date():
    df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20170301", end_date='20210907', adjust="qfq")
    print(df.head(2))


def test_ak_minute():
    df = ak.index_zh_a_hist_min_em(symbol="000016", period="1", start_date="2022-05-01 09:32:00", end_date="2022-12-01 09:32:00")
    data = format_minute_ak(df,'000016')
    # 这个时间转日期有问题，改用下面的
    # data['trade_date'] = data['trade_time'].map(lambda x: x.replace('-', '')[0:8])
    # print(data['trade_time'].dtypes)
    data['trade_date'] = data['trade_time'].apply(lambda x:x.strftime('%Y%m%d'))

    # df_n1b[name] = df_n1b.apply(lambda x: n1b_map.get(x['trade_date'], 0), axis=1)
    print(data.head(2))

def test_stock():
    # get_stock_strong_days()
    #
    # get_selected()
    return True

# test_ak()

# test_ak_date()

# test_ak_minute()

data_path = r"D:\usr\ts_data_czsc"
dc = TsDataCache(data_path=data_path)
df = dc.get_all_ths_members(exchange="A", type_="N")
