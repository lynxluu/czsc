import tushare as ts
import pandas as pd

def get_k():
    code='600519'
    ktype='5'
    autype='qfq'
    start=None
    end=None
    retry_count=3

    # 使用get_hist_data()函数获取K线数据
    # df1 = ts.get_hist_data('600519')
    # df1 = ts.get_hist_data(code=code, ktype=ktype,)
    # print(len(df1), '\n', df1.columns, '\n', df1.tail())

    # 使用get_k_data()函数获取K线数据
    # 需要修改 C:\Python\Python38-32\lib\site-packages\tushare\stock\trading.py 706行的代码
            # df = _get_k_data(url, dataflag, symbol, code, index, ktype, retry_count, pause)
            # data = pd.concat([data,df])
    # df2 = ts.get_k_data('600519')
    # print(len(df2), df2.head())

    # 打印前5行数据
    # ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'turnoverratio', 'code']
    df3 = ts.get_k_data(code='600519', ktype='5', autype='qfq', start=None, end=None, retry_count=3, )
    print(len(df3), '\n', df3.columns, '\n', df3.tail())

def get_symbols():
    # 获取沪市所有股票代码
    sh_stock = ts.get_stock_basics()
    sh_stock = sh_stock.reset_index()
    sh_stock['code'] = sh_stock['code'].apply(lambda x: 'sh' + x)

    # 获取深市所有股票代码
    sz_stock = ts.get_stock_basics('2019-12-31', 'S')
    sz_stock = sz_stock.reset_index()
    sz_stock['code'] = sz_stock['code'].apply(lambda x: 'sz' + x)

    # 合并沪深两市股票代码
    all_stock = pd.concat([sh_stock, sz_stock], axis=0, ignore_index=True)

    # 获取沪市指数代码
    sh_index = ts.get_hs300s()
    sh_index['code'] = sh_index['code'].apply(lambda x: 'sh' + x)

    # 获取深市指数代码
    sz_index = ts.get_sz50s()
    sz_index['code'] = sz_index['code'].apply(lambda x: 'sz' + x)

    # 合并沪深两市指数代码
    all_index = pd.concat([sh_index, sz_index], axis=0, ignore_index=True)

    # 获取基金代码
    all_fund = ts.fund_basic()
    all_fund = all_fund.reset_index()
    all_fund['ts_code'] = all_fund['ts_code'].apply(lambda x: x.split('.')[0])

    # 合并所有股票、指数和基金代码
    all_codes = pd.concat([all_stock[['code', 'name']], all_index[['code', 'name']], all_fund[['ts_code', 'name']]],
                          axis=0, ignore_index=True)
    all_codes.columns = ['code', 'name']

    return all_codes

symbols = get_symbols()
print(len(symbols), symbols.head(), symbols.tail())