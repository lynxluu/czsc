import akshare as ak

def get_kline_data(symbol, freq, adj, sdt=None, edt=None, limit=200):
    """
    获取K线数据    :param symbol: 股票代码，格式类似aaaaaa.bb#cc，aa表示代码，bb表示市场，cc表示类型股票E，指数I，基金FD，期货FT
    :param freq: K线的时间周期，例如1min表示1分钟K线，D表示日K线
    :param adj: 复权方式，例如'qfq'表示前复权，'hfq'表示后复权，None表示不复权
    :param sdt: 开始时间，格式为YYYY-MM-DD，例如'2021-01-01'，默认为None
    :param edt: 结束时间，格式为YYYY-MM-DD，例如'2021-06-14'，默认为None
    :param limit: 取最近的K线个数，例如100表示取最近的100根K线， 默认为200
    :return: 包含K线数据的dataframe，包含列为'dt', 'symbol', 'freq', 'open', 'high', 'low', 'close', '', 'amount', 'elements'
    """
    # 获取K线数据
    df = ak.stock_zh_a_hist(symbol=symbol, period=freq, adjust=adj, start_date=sdt, end_date=edt)
    # ak.stock_zh_a_spot_em()

    # 取最近的K线个数
    if limit is not None:
        df = df.tail(limit)

    # 重命名列名
    df = df.rename(columns={'date': 'dt', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'vol', 'amount': 'amount'})

    # 添加自定义的elements列
    df['elements'] = [0, 1, 0] * len(df)

    return df[['dt', 'symbol', 'freq', 'open', 'high', 'low', 'close', 'vol', 'amount', 'elements']]
