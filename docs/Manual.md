# czsc学习
https://github.com/waditu/czsc

pip install czsc -U -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com  --upgrade
pip install akshare -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com  --upgrade

学缠论需要点悟性，心法比技法重要。推荐阅读：《缠中说禅经济学》、《论语详解》，只读《教你炒股票》大概率是学不会缠论的。


## 改写tushare-akshare

https://tushare.pro/document/2?doc_id=109

https://www.akshare.xyz/data/stock/stock.html#id18

### tushare写法

通用行情接口
```python
https://tushare.pro/document/2?doc_id=109

#取000001的前复权行情
df = ts.pro_bar(ts_code='000001.SZ', adj='qfq', start_date='20180101', end_date='20181011')

trade_date  ts_code trade_date     open     high      low    close  \
20181011    000001.SZ   20181011  1085.71  1097.59  1047.90  1065.19
20181010    000001.SZ   20181010  1138.65  1151.61  1121.36  1128.92
20181009    000001.SZ   20181009  1130.00  1155.93  1122.44  1140.81
20181008    000001.SZ   20181008  1155.93  1165.65  1128.92  1128.92
20180928    000001.SZ   20180928  1164.57  1217.51  1164.57  1193.74
```

tushare 获取股票行情接口
```python
https://tushare.pro/document/2?doc_id=27

pro = ts.pro_api()
df = pro.query('daily', ts_code='000001.SZ', start_date='20180701', end_date='20180718')
```
### akshare写法
需要仿照ts写个 ts.pro_bar函数

需要统一数据格式

#### 1）股票--历史行情数据-通用
接口: index_zh_a_hist

```python
import akshare as ak

stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20170301", end_date='20210907', adjust="qfq")
print(stock_zh_a_hist_df)

           日期     开盘   收盘    最高  ...   振幅  涨跌幅 涨跌额 换手率
0     2017-03-01   8.65   8.65   8.71  ...  0.93  0.12  0.01  0.21
1     2017-03-02   8.67   8.59   8.70  ...  1.39 -0.69 -0.06  0.24
2     2017-03-03   8.57   8.56   8.59  ...  0.81 -0.35 -0.03  0.20
3     2017-03-06   8.56   8.61   8.62  ...  0.82  0.58  0.05  0.24
4     2017-03-07   8.60   8.61   8.62  ...  0.70  0.00  0.00  0.17
          ...    ...    ...    ...  ...   ...   ...   ...   ...
1100  2021-09-01  17.48  17.88  17.92  ...  5.11  0.45  0.08  1.19
1101  2021-09-02  18.00  18.40  18.78  ...  5.48  2.91  0.52  1.25
1102  2021-09-03  18.50  18.04  18.50  ...  4.35 -1.96 -0.36  0.72
1103  2021-09-06  17.93  18.45  18.60  ...  4.55  2.27  0.41  0.78
1104  2021-09-07  18.60  19.24  19.56  ...  6.56  4.28  0.79  0.84
```
2）分时行情数据
接口: index_zh_a_hist_min_em

目标地址: http://quote.eastmoney.com/center/hszs.html

```python
import akshare as ak

index_zh_a_hist_min_em_df = ak.index_zh_a_hist_min_em(symbol="000016", period="1", start_date="1979-09-01 09:32:00", end_date="2222-01-01 09:32:00")
print(index_zh_a_hist_min_em_df)

           时间       开盘       收盘  ...     成交量           成交额       最新价
0     2022-02-15 09:30:00     0.00  3101.36  ...  145226  3.321566e+08  3104.273
1     2022-02-15 09:31:00     0.00  3106.01  ...  495049  1.174811e+09  3108.621
2     2022-02-15 09:32:00     0.00  3107.55  ...  361315  7.954516e+08  3110.788
3     2022-02-15 09:33:00     0.00  3104.50  ...  402809  6.602538e+08  3108.281
4     2022-02-15 09:34:00     0.00  3101.29  ...  358263  8.060021e+08  3106.361
                   ...      ...      ...  ...     ...           ...       ...
1200  2022-02-21 14:56:00  3145.98  3146.37  ...  145263  3.190067e+08  3156.906
1201  2022-02-21 14:57:00  3146.36  3147.00  ...  165207  3.131019e+08  3157.498
1202  2022-02-21 14:58:00  3146.65  3146.90  ...   10518  1.861847e+07  3157.538
1203  2022-02-21 14:59:00  3146.90  3146.90  ...       0  0.000000e+00  3157.538
1204  2022-02-21 15:00:00  3144.86  3144.86  ...  367925  6.682456e+08  3155.529
```

3）指数--历史行情数据-通用 
接口: index_zh_a_hist

```python   
import akshare as ak

index_zh_a_hist_df = ak.index_zh_a_hist(symbol="000016", period="daily", start_date="19700101", end_date="22220101")
print(index_zh_a_hist_df)

       日期       开盘       收盘       最高  ...   振幅   涨跌幅 涨跌额   换手率
0     2004-01-02   997.00  1011.35  1021.57  ...  0.00  0.00   0.00  0.00
1     2004-01-05  1008.28  1060.80  1060.90  ...  5.20  4.89  49.45  0.00
2     2004-01-06  1059.14  1075.66  1086.69  ...  2.60  1.40  14.86  0.00
3     2004-01-07  1075.56  1086.30  1095.84  ...  2.31  0.99  10.64  0.00
4     2004-01-08  1087.68  1102.66  1108.29  ...  2.37  1.51  16.36  0.00
          ...      ...      ...      ...  ...   ...   ...    ...   ...
4400  2022-02-15  3101.36  3119.93  3126.42  ...  0.95  0.51  15.93  0.24
4401  2022-02-16  3134.88  3136.08  3150.86  ...  0.70  0.52  16.15  0.20
4402  2022-02-17  3138.77  3139.18  3156.87  ...  0.79  0.10   3.10  0.20
4403  2022-02-18  3126.28  3162.82  3162.82  ...  1.30  0.75  23.64  0.19
4404  2022-02-21  3155.32  3144.86  3155.88  ...  0.86 -0.57 -17.96  0.21
```
4) 指数--分时行情数据
接口: index_zh_a_hist_min_em
```python
import akshare as ak

index_zh_a_hist_min_em_df = ak.index_zh_a_hist_min_em(symbol="000016", period="1", start_date="1979-09-01 09:32:00", end_date="2222-01-01 09:32:00")
print(index_zh_a_hist_min_em_df)

             时间       开盘       收盘  ...     成交量           成交额       最新价
0     2022-02-15 09:30:00     0.00  3101.36  ...  145226  3.321566e+08  3104.273
1     2022-02-15 09:31:00     0.00  3106.01  ...  495049  1.174811e+09  3108.621
2     2022-02-15 09:32:00     0.00  3107.55  ...  361315  7.954516e+08  3110.788
3     2022-02-15 09:33:00     0.00  3104.50  ...  402809  6.602538e+08  3108.281
4     2022-02-15 09:34:00     0.00  3101.29  ...  358263  8.060021e+08  3106.361
                   ...      ...      ...  ...     ...           ...       ...
1200  2022-02-21 14:56:00  3145.98  3146.37  ...  145263  3.190067e+08  3156.906
1201  2022-02-21 14:57:00  3146.36  3147.00  ...  165207  3.131019e+08  3157.498
1202  2022-02-21 14:58:00  3146.65  3146.90  ...   10518  1.861847e+07  3157.538
1203  2022-02-21 14:59:00  3146.90  3146.90  ...       0  0.000000e+00  3157.538
1204  2022-02-21 15:00:00  3144.86  3144.86  ...  367925  6.682456e+08  3155.529

```



1）处理日期报错，加errors='coerce'参数解决
pd.to_datetime(df['trade_date'], format='%Y%m%d',errors='coerce')

2）日期排序报错
```ini
File "E:\usr\git\czsc\czsc\data\ts_cache.py", line 32, in update_bars_return
 assert kline['dt'][0] < kline['dt'][1], "kline 必须是时间升序"

ts.py中
    dt_key = 'trade_time' if '分钟' in freq.value else 'trade_date'
    kline = kline.sort_values(dt_key, ascending=True, ignore_index=True)

dt=pd.to_datetime(record[dt_key])
```

3)KeyError: 'trade_date'

```python
stocks.py
df_alpha = df_n1b[['trade_date', beta_name, 'selector']]


    def validate_performance(sel

 	df_n1b = pd.DataFrame({"trade_date": pd.to_datetime(dc.get_dates_span(sdt, edt))})
        	df_n1b[name] = df_n1b.apply(lambda x: n1b_map.get(x['trade_date'], 0), axis=1)
```

4）接口无法访问
```ini
Exception: 抱歉，您没有访问该接口的权限，权限的具体详情访问：https://tushare.pro/document/1?doc_id=108。
get_share_strong_days error: 000517.SZ, 荣安地产
Traceback (most recent call last):
  File "E:\usr\git\czsc\czsc\sensors\stocks.py", line 366, in get_stock_strong_days
    dfs, n_bars = self.get_share_strong_days(ts_code, name)
  File "E:\usr\git\czsc\czsc\sensors\stocks.py", line 348, in get_share_strong_days
    df_ = dc.daily_basic(ts_code, sdt, dc.edt)

实际上是这个函数报错
ts_cache.daily_basic(ts_code, sdt, dc.edt)

试着在ak.py里写一个ak_daily_basic函数
df = ak_daily_basic(ts_code=ts_code, start_date=start_date_, end_date="20300101")

名称	类型	描述
ts_code	str	TS股票代码
trade_date	str	交易日期  stock_a_lg_indicator
close	float	当日收盘价  stock_zh_a_hist
turnover_rate	float	换手率（%） stock_zh_a_hist
turnover_rate_f	float	换手率（自由流通股） 可计算
volume_ratio	float	量比  stock_zh_a_spot_em
pe	float	市盈率（总市值/净利润， 亏损的PE为空）  stock_a_lg_indicator
pe_ttm	float	市盈率（TTM，亏损的PE为空） stock_a_lg_indicator
pb	float	市净率（总市值/净资产） stock_a_lg_indicator
ps	float	市销率  stock_a_lg_indicator
ps_ttm	float	市销率（TTM） stock_a_lg_indicator
dv_ratio	float	股息率 （%）stock_a_lg_indicator
dv_ttm	float	股息率（TTM）（%）stock_a_lg_indicator
total_share	float	总股本 （万股）
float_share	float	流通股本 （万股）
free_share	float	自由流通股本 （万）
total_mv	float	总市值 （万元） stock_a_lg_indicator
circ_mv	float	流通市值（万元）  

```

5) 使用pickle.load(f)加载pickle文件时，报错：EOFError: Ran out of input.
```bash
原因:断网或者磁盘满导致下载文件为空
方法:加载前判断文件是否为空

File "D:\usr\git\czsc\czsc\utils\io.py", line 28, in read_pkl
    data = pickle.load(f)
EOFError: Ran out of input

```
### 已实现功能

pro.ths_daily   获取同花顺概念板块的日线行情

pro.ths_index   获取同花顺概念

pro.ths_member  获取同花顺概念成分股

ts.pro_bar      获取日线以上数据
-- ak_pro_bar

pro.stock_basic 获取基础信息数据    
## 注册tushare社区后，修改个人信息，获得120积分即可访问。不用自己实现

```python
# AK
ak.stock_individual_info_em(symbol="000001")

 item                value
0   总市值  337468917463.220032
1  流通市值      337466070320.25
2    行业                   银行
3  上市时间             19910403
4  股票代码               000001
5  股票简称                 平安银行
6   总股本        19405918198.0
7   流通股        19405754475.0

# TS

pro.query('stock_basic', exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')

  ts_code     symbol     name     area industry    list_date
0     000001.SZ  000001  平安银行   深圳       银行  19910403
1     000002.SZ  000002   万科A   深圳     全国地产  19910129
2     000004.SZ  000004  国农科技   深圳     生物制药  19910114
3     000005.SZ  000005  世纪星源   深圳     房产服务  19901210
```

pro.trade_cal   交易日历

pro.hk_hold 沪深港股通持股明细

pro.cctv_news   新闻联播

pro.index_weight  指数成分和权重


pro.limit_list  每日涨跌停统计

pro.daily_basic_new 每日指标



## 掘金量化配置

https://www.myquant.cn/

注册,后查询自己的token 
fd9908c8715288e7af1316d9ff7be6a8709385b3

### debug
```ini
#### 问题1
C:\Users\admin\gm_token.txt 文件不存在，请单独启动一个 python 终端，调用 set_gm_token 方法创建该文件，再重新执行。
新建gm_token.txt文件 把token放进去

#### 问题2
UnicodeEncodeError: 'locale' codec can't encode character '\u5e74' in position 2: encoding error

#### 问题3
No objects to concatenate
File "E:\usr\git\czsc\czsc\data\ts_cache.py", line 276, in pro_bar_minutes
    df_klines = pd.concat(klines, ignore_index=True)

#### 问题4
为什么有时候设置了sdt和edt 后面还要重新设置？
默认sdt和edt间隔过大，np的有些函数会超出范围，缩小一些范围让np不报错
```

## 新功能

### python读取配置文件

Python常用配置文件ini、json、yaml读写总结

https://cloud.tencent.com/developer/article/1762055


from czsc import signals
from czsc.traders.ts_backtest import TsDataCache
from czsc.data import config

paras = config.yaml_config()['dev']
data_path = paras['data_path']
sdt = paras['sdt']
edt = paras['edt']
dc = TsDataCache(data_path=data_path, sdt=sdt, edt=edt)