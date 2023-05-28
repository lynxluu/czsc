import tushare as ts

# 使用get_hist_data()函数获取K线数据
df1 = ts.get_hist_data('600519')

# 使用get_k_data()函数获取K线数据
# 需要修改 C:\Python\Python38-32\lib\site-packages\tushare\stock\trading.py 706行的代码
        # df = _get_k_data(url, dataflag, symbol, code, index, ktype, retry_count, pause)
        # data = pd.concat([data,df])
df2 = ts.get_k_data('600519')

# 打印前5行数据
print(df1.head())
print(df2.head())
