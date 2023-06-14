import requests

def get_dfcf1():
    # 设置API接口地址和参数
    api_url = "http://push2.eastmoney.com/api/qt/stock/trends2/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f27,f28",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "ndays": "1",
        "iscr": "0",
        "secid": "1.000001",
        "cb": "jsonp1600581525000",
    }

    # 发送API请求并解析响应数据
    response = requests.get(api_url, params=params)
    print(response)
    data = response.json()

    # 提取分时数据
    trend = data.get("data", {}).get("trends")
    if trend:
        for item in trend:
            print(item)

def get_dfcf2():
    import requests
    import pandas as pd

    url = 'http://push2.eastmoney.com/api/qt/stock/trends2/get'
    params = {
        'fields1': 'f1,f2,f3,f4,f5,f6',  # 需要获取的字段
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',  # 扩展字段
        'ut': 'fa5fd1943c7b386f172d6893dbfba10b',  # 设备标识
        'ndays': '50',  # 获取最近n天的数据
        'iscr': '1',  # 分钟走势 1表示5分钟
        'secid': '000001.SH',  # 股票代码
        'klt': '101',  # 数据详细级别 101表示5分钟
        'fqt': '1',  # 复权类型:1不复权,2前复权,3后复权
    }

    r = requests.get(url, params)
    print(r, r.url)
    data = r.json()

    # 转化为DataFrame
    df = pd.DataFrame(data['data']['trends'])
    df.index = pd.to_datetime(df.loc[:, 'fqtime'], unit='ms')  # 转化index为datetime

    # 将列名转为中文
    df.columns = ['时间', '开盘价', '最高价', '最低价', '收盘价', '成交量', '成交额']

    print(df.head())
    return df

res = get_dfcf2()