import tushare as ts
import pandas as pd

def get_bars_v1(symbol, freq):
    # 使用get_k_data()函数获取K线数据
    # 需要修改 C:\Python\Python38-32\lib\site-packages\tushare\stock\trading.py 706行的代码
            # df = _get_k_data(url, dataflag, symbol, code, index, ktype, retry_count, pause)
            # data = pd.concat([data,df])

    symbol_ = symbol.split('#')
    if len(symbol_) == 2:
        ts_code, asset = symbol_
    else:
        ts_code, asset = symbol_[0], 'E'

    code = ts_code.split('.')[0]
    index = True if asset == 'I' else False
    ktype = freq.replace('min', '') if 'min' in freq else freq
    start = '2023-01-01'

    # df = ts.get_k_data('000001',ktype='D')
    # df = ts.get_k_data(code=code, ktype=ktype)
    df = ts.get_k_data(code=code, ktype=ktype, index=index, autype=adj)


    # 使用get_hist_data()函数获取K线数据
    # df = ts.get_hist_data('600519')

    # df = ts.get_hist_data(code=code, ktype=ktype, start=start)

    # print(len(df), df.head())
    # 打印前5行数据
    # ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'turnoverratio', 'code']
    # df3 = ts.get_k_data(code='600519', ktype='5', autype='qfq', start=None, end=None, retry_count=3, )
    # print(len(df3), '\n', df3.columns, '\n', df3.tail())
    return df

def get_stock():
    # 获取沪市所有股票代码
    pro = ts.pro_api()
    df = pro.query('stock_basic', exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    df['symbol'] = df['ts_code']+'#E'

    df.to_csv('_stocks.csv')
    return df

def get_fund():
    pro = ts.pro_api()
    df = pro.fund_basic(market='E')
    df['symbol'] = df['ts_code'] + '#FD'

    df.to_csv('_funds.csv')
    return df

def get_index():
    pro = ts.pro_api()
    # 获取申万一级、二级、三级行业列表 level='L2' L1 L3
    # df = pro.index_classify(level='L2', src='SW2021')
    df = pro.index_basic(market='SW', category='二级行业指数')
    # df = pro.index_basic(market='CSI', category='二级行业指数')
    df['symbol'] = df['ts_code'] + '#I'

    df.to_csv('_indexs.csv')
    return df


def get_ft():
    # 初始化pro接口
    pro = ts.pro_api()

    # 获取铁矿石期货的交易所代码
    # df = pro.fut_basic(exchange='DCE', fut_type='2', fields='ts_code,symbol,name,list_date,delist_date')

    ts_code = 'IL9'
    freq = '30min'
    # fut_daily 日线， ft_mins 分时获取铁矿石期货的30分钟行情数据
    # df = pro.fut_daily(ts_code=ts_code)
    # df = pro.ft_mins(ts_code=ts_code, freq='30min')
    df = pro.ft_mins(ts_code=ts_code, start_date='20230501', end_date='20230606', freq=freq, limit=200)

    return df


def get_bars(symbol=None, freq='D', limit=200):

    if not symbol:
        # 默认是中证银行指数
        symbol = '399986.CSI#I'
        freq = '30min'

    symbol_ = symbol.split('#')
    if len(symbol_) == 2:
        ts_code, asset = symbol_
    else:
        ts_code, asset = symbol_[0], 'E'

    # ts_code, asset = symbol_ if len(symbol_) == 2 else symbol_[0], 'E'

    # 获取中证银行指数的日线K线数据
    pro = ts.pro_api()
    df = ts.pro_bar(ts_code=ts_code, asset=asset, freq=freq, limit=limit)

    # # 转换时间字段为datetime格式
    # df['trade_date'] = pd.to_datetime(df['trade_date'])

    # 选取需要的字段
    # fields = ['trade_date', 'open', 'high', 'low', 'close', 'vol']
    # df = df[fields]

    # # 按时间排序
    # df = df.sort_values('trade_date')

    # 输出结果
    # print(df)

    return df

# res = get_stock()
# res = get_index()
# res = get_fund()
# res = get_ft()
# res = get_bar()


# symbol, freq, adj, limit = '399986.CSI#I', '30min', 'qfq', 200
symbol, freq, adj, limit = '002624.SZ#E', 'D', 'qfq', 200

res = get_bars_v1(symbol, freq)

# res = get_bars(symbol, freq)
# res = get_bars('399986.CSI#I','D')
# res = get_bars('002624.SH','30min')

# pro = ts.pro_api()
# res = ts.pro_bar(ts_code=symbol, freq=freq, limit=limit)

print(len(res), res.columns, )
# if not res.empty:
#     print(res.iloc[-1].to_dict())

# for index, row in res.iterrows():
#     print(row.to_dict())

print(res)