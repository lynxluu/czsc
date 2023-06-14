import akshare as ak
import pandas as pd


FreqD = {
    '1min': '1',
    '5min': '5',
    '15min': '15',
    '30min': '30',
    '60min': '60',
    'D': 'daily',
    'W': 'weekly',
    'M': 'monthly'
}

def get_bars(symbol, freq='D', adj='qfq', sdt=None, edt=None,limit=200):
    """
    获取指定股票的k线数据

    :param symbol: str, 股票代码，格式如aaaaaa.bb#cc，aa表示代码，bb表示市场，cc表示类型股票E，指数I，基金FD，期货FT
    :param freq: str, 频率，有'5min' ,'15min', '30min', '60min', 'D', 'W', 'M'几种。
    :param adj: str, 复权方式，有'qfq', 'hfq', None三种。
    :param sdt: str, 开始时间，格式为'YYYY-MM-DD'，默认为None，表示从最早数据开始获取
    :param edt str 结束时间，格式为'YYYY-MM-DD'，默认为None，表示获取到最新的数据
    :param limit: int, 取最近的k线个数，默认为None，表示获取所有数据
    :return: pd.DataFrame, k线数据
    """
    # 对symbol进行处理，取得 aaaaaa作为 ts_code 取得cc作为 asset
    # ts_code, asset = symbol.split('#')
    ts_code = symbol.split('.')[0]
    asset = symbol.split('#')[1]
    period = FreqD[freq]

    # 获取数据
    if 'min' in freq:
        df = ak.stock_zh_a_hist_min_em(symbol=ts_code, period=period, adjust=adj, start_date=sdt, end_date=edt)
        # df = ak.stock_zh_a_hist_min_em(symbol=ts_code, period=period)
    else:
        print(ts_code,period,adj,sdt,edt)
        df = ak.stock_zh_a_hist(symbol=ts_code, period=period, adjust=adj, start_date=sdt, end_date=edt)
        # df = ak.stock_zh_a_hist(symbol=ts_code, period=period, adjust=adj)

    #最近的k个数
    if limit:
        df = df.tail(limit)

    # print(df.columns,df.tail(1))
    # 对df进行重命名
    df = df.rename(columns={'日期': 'dt', '开盘':'open','收盘':'close','最高':'high','最低':'low','涨跌幅':'zdf','涨跌额':'zde','成交量':'vol','成交额': 'amount','振幅': 'zf','换手率': 'hs'})

    # 日期统一处理，排序
    df = df.rename(columns={'时间': 'dt'})
    df['dt'] = pd.to_datetime(df['dt'], format="%Y-%m-%d %H:%M:%S")
    df = df.sort_values('dt')

    df['symbol'] = ts_code
    df['freq'] = freq
    df['elements'] = [[0,1,0]] * len(df)

    fields = ['dt', 'symbol', 'freq', 'open', 'high', 'low', 'close', 'vol', 'amount', 'elements']
    df = df[fields]

    return df


res = get_bars('000001.SH#I','60min')
# res = get_bars('000001.SH#I','D')
print(len(res), res)