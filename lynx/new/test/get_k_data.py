import tushare as ts
import pandas as pd

def get_k():
    code='600519'
    ktype='5'
    autype='qfq'
    start=None
    end=None
    # retry_count=3

    # 使用get_hist_data()函数获取K线数据
    # df1 = ts.get_hist_data('600519')
    # df1 = ts.get_hist_data(code=code, ktype=ktype,)
    # print(len(df1), '\n', df1.columns, '\n', df1.tail())

    # 使用get_k_data()函数获取K线数据
    # 需要修改 C:\Python\Python38-32\lib\site-packages\tushare\stock\trading.py 706行的代码
            # df = _get_k_data(url, dataflag, symbol, code, index, ktype, retry_count, pause)
            # data = pd.concat([data,df])
    df2 = ts.get_k_data('000001',ktype='D')
    print(len(df2), df2.head())

    # 打印前5行数据
    # ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'turnoverratio', 'code']
    # df3 = ts.get_k_data(code='600519', ktype='5', autype='qfq', start=None, end=None, retry_count=3, )
    # print(len(df3), '\n', df3.columns, '\n', df3.tail())

def get_stock():
    # 获取沪市所有股票代码
    pro = ts.pro_api()
    df = pro.query('stock_basic', exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    df['symbol'] = df['ts_code']+'#E'

    return df

def get_fund():
    pro = ts.pro_api()
    df = pro.fund_basic(market='E')
    df['symbol'] = df['ts_code'] + '#FD'

    return df

def get_index():
    pro = ts.pro_api()
    # 获取申万一级、二级、三级行业列表 level='L2' L1 L3
    # df = pro.index_classify(level='L2', src='SW2021')
    # df = pro.index_basic(market='SW', category='二级行业指数')
    df = pro.index_basic(market='CSI', category='二级行业指数')
    df['symbol'] = df['ts_code'] + '#I'

    return df

# res = get_stock()
res = get_index()
# res = get_fund()

print(len(res), res.columns, )
# if not res.empty:
#     print(res.iloc[-1].to_dict())

# for index, row in res.iterrows():
#     print(row.to_dict())

print(res)