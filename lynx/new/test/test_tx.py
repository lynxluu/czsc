import requests
import pandas as pd

'''
要使用https://web.ifzq.gtimg.cn/appstock/app/kline/kline获取股票k线数据，您需要构造以下请求参数：
code：股票代码，以'sh''sz'开头，后面跟着6位数字。例如，'sh000001'代表上证指数，'sz000002'代表万科A股票。
k_type：时间周期，可以是'1'、'5'、'15'、'30'、'60'、'120'、'240'、'D'、'W'、'M'之一。分别代表1分钟、5分钟、15分钟、30分钟、60分钟、120分钟、240分钟、日线、周线、月线。
fqt：复权类型，可以是'0'、'1'、'2'之一。分别代表不复权、前复权、后复权。
start：开始时间，格式为'YYYYMMDD'。例如，'20210615'代表2021年6月15日。
end：结束时间，格式为'YYYYMMDD'。例如，'20210630'代表2021年6月30日。
max_count：最大数据条数，最多可以获取320条数据。如果不指定此参数，则默认获取最近的320条数据。
'''

def get_tx1():
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    # 设置请求参数
    params = {
        'code': 'sh000001',
        'k_type': 'm30',
        'fqt': '0',
        'start': '20230101',
        'end': '20230614'
    }

    # 发送请求
    response = requests.get('https://web.ifzq.gtimg.cn/appstock/app/kline/mkline', headers=headers, params=params)

    # 解析响应数据
    print(response.json())
    data = response.json()['data']['kline']
    df = pd.DataFrame([kline.split(',') for kline in data], columns=['timestamp', 'open', 'close', 'high', 'low', 'volume', 'amount', 'unknown'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    df = df.astype(float)

    # 输出结果
    print(df)

def get_tx2():
    import requests
    import pandas as pd
    from datetime import datetime, timedelta

    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    # 计算3个月前的日期
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')

    # 设置请求参数
    params = {
        'code': 'sh000001',
        'k_type': '30',
        'fqt': '1',
        'start': start_date_str,
        'end': end_date_str
    }

    # 发送请求
    response = requests.get('https://web.ifzq.gtimg.cn/appstock/app/kline/mkline', headers=headers, params=params)

    # 解析响应数据
    print(response.json())
    data = response.json()['data']['sh000001']['day']
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'close', 'high', 'low', 'volume', 'amount'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    df = df.astype(float)

    # 输出结果
    print(df)


get_tx1()