gpt脚本：

## 腾讯接口
哪里能找到https://web.ifzq.gtimg.cn/appstock/app/kline/kline这个接口的使用手册

参考这篇
https://blog.csdn.net/geofferysun/article/details/114752182
https://www.cnblogs.com/interdrp/p/14159671.html

详情
http://qt.gtimg.cn/q=s_sh600519
http://qt.gtimg.cn/q=sh600519


日线数据
接口1
/1.https://web.ifzq.gtimg.cn/appstock/app/fqkline/get 固定访间链接
/2.param=代码，日k,开始日期，结束日期，获取多少个交易日，前复权
/2.1 usAAPL.0Q股票代码，这里是us是美股，AAPL是苹果，“.0Q"是美股拼接后缀，其他不需要拼接
/2.2500代表获取多少个交易日，500实际查出来的是501条数据，多一条
/2.3qfq前复权
/上海，茅台【sh600519】 y
https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600519,day,2020-3-1,2021-3-1,500,qfq
/港股，小米【hk01810】 y
https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=hk01810,day,2020-3-1,2021-3-1,500,qfq
/美股，苹果【usAAPL】，需要拼接".OQ”
https //web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=usAAPL.0Q,day,2020-3-1,2021-3-1,500,qfq

接口2
//日K后复权 y
//320代表查询几天的历史数据,1年为320两年为640， //美股需要拼接“.0Q”
https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayhfq&param=sh600519,day,,,320,hfq&r=0.9866

一天内的1分钟分时行情 y
https://web.ifzq.gtimg.cn/appstock/app/minute/query?code=sh600519


1分钟 n
https://web.ifzq.gtimg.cn/appstock/app/kline/mkline?param=sh600519,m1,,32000
//5分钟
https://web.ifzq.gtimg.cn/appstock/app/kline/mkline?param=sh600519,m5,,32000
//15分钟
https://web.ifzq.gtimg.cn/appstock/app/kline/mkline?param=sh600519,m15,,32000
/30分钟
https://web.ifzq.gtimg.cn/appstock/app/kline/mkline?param=sh600519,m30,,32000
//60分钟
https://web.ifzq.gtimg.cn/appstock/app/kline/mkline?param=sh600519,m60,,32000

https://web3.ifzq.gtimg.cn/appstock/app/kline/mkline?param=sh600519,m30,20220101,20220131,640


//5日分时 y
https://web.ifzq.gtimg.cn/appstock/app/day/query?code=sh600519

//TOD0美股拼接需要us,后缀有的需要拼接“.0Q”,这里我还没搞明白规则 y
https://web.ifzq.gtimg.cn/appstock/app/dayus/query?code=us.DJI
https://web.ifzq.gtimg.cn/appstock/app/dayus/query?code=usGOOD.0Q

//美股分时，以Google请求为例： y
/l.minute改为：UsMinute
//2.股票代码需要拼接“.0Q”
https://web.ifzq.gtimg.cn/appstock/app/UsMinute/query?code=usGOOG.0Q

## akshare

## tushare

## 聚宽
可以试用3个月

## 雅虎财经

https://query1.finance.yahoo.com/v8/finance/chart/000001.SS?interval=30m&range=60d

## 原始k线 bars
定义一个函数，
输入: symbol, freq, adj,sdt,edt,limit
symbol 类型字符串，格式如aaaaaa.bb#cc，aa表示代码，bb表示市场，cc表示类型股票E，指数I，基金FD，期货FT.
对symbol要进行处理，取得 aaaaaa.bb作为 ts_code， 取得cc作为 asset
freq 类型字符串，表示频率，有'5min' ,'15min', '30min', '60min', 'D',' 'W','M'几种。
adj 类型字符串，表示复权方式 有'qfq', 'hfq', None三种。
sdt,edt 表示开始时间和结束时间，可以不输入
limit 为整数，表示取最近的k线个数
输出：一组dataframe格式的k线

接收输入参数（ts_code，asset， freq, adj,sdt,edt,limit），从akshare接口获取df后，(akshare输出的df列不一定相同)对df进行处理，使得他包含下列列的k线，返回输出
'dt', 'symbol', 'freq', 'open', 'high', 'low', 'close', 'vol', 'amount', 'elements'
elements是自定义的整数列表 =[0,1,0]


## 包含关系：
输入：两根k线k1,k2
输出：true表示包含，false表示不包含
如果两根k线k1,k2, 满足情况1， 称为k1包含k2；满足情况2，称为k2包含k1
情况1：k1的高点大于或等于k2的高点，且k1的低点小于或等于k2的低点
情况2：k1的高点小于或等于k2的高点，且k1的低点大于或等于k2的低点


### 去除包含关系：
输入：3根k线k1, k2，k3
输出：k2，k3有包含关系，则计算k4并返回，否则返回k3
算法：
比较k2，k3
#### 如果有包含关系, 则创建新k4,  给k4的列赋值，返回k4
 'dt' , 'symbol', 'freq', 'open', 'high', 'low', 'close', 'vol', 'amount', 'elements'

不变（取k2值)：'symbol', 'freq'
合并（k2,k3的值相加）:  'vol' 'amount'

1a) 方向是up, 
取高（k2,k3的值取高）:'dt' 'high'  'low'
特殊计算 'elements'

1b) 方向是down
取低 （k2,k3的值取低）:'dt' 'high'  'low'
特殊计算 'elements'
#### 如果没有包含关系，返回k3


## 新k线 n_bars：
输入：原始k线 bars
输出：处理过包含关系的k线 n_bars

从原始k线bars 取前2根k线k1,k2，
如果不包含且k1.high不等于k2.high，则将他们放入n_bars，
否则，继续循环向下取k1，k2，直到不包含。

如果k1.high大于k2.high 方向是up，
否则方向是down
再依次取下一根k线k3，对k2，k3进行判断 

### 1）有包含关系, 则创建新k4加入n_bars
### 2) 没包含关系，k3加入n_bars

循环直到处理完所有bars

## 分型：
输入n_bars，输出一个fx列表fxs
从n_bars循环取三根k线k1,k2,k3，判断是否分型
是的话，返回一个dataframe类型的fx，包含以下列
symbol dt  fx, high low  mark elements

symbol dt: 取k2对应的值
elements = [k1,k2,k3]列表
### 如果k2的高最高且k2的低也最高，则是顶分型.
	fx = k2.high
	high = fx
	low = k1和k3的low取低
	mark = 'G'

### 如果k2的低最低且k2的高也最低，则是底分型.
	fx = k2.low
	high = k1和k3的high取高
	low = fx
	mark = 'D'
	
### 将fx加入fxs列表

循环直到处理完所有n_bars， 得到一个fxs列表

## 笔：

### 定义：
1）两个相反类型的分型fx_a, fx_b 连接，
2）分型之间的n_bars数量>=4
3）分型之间的bars数量>=5
#### 4a)上升笔
fx_a的高小于 fx_b的高，且fx_a的低 小于 fx_b的低
bi后的fx点不能大于fx_b的fx点
#### 4b)下降笔
x_a的高大于 fx_b的高，且fx_a的低 大于 fx_b的低
bi后的fx点不能小于fx_b的fx点

### 算法：
输入fxs，输出笔；
循环取fxs中的两个分型fx1,fx2
#### 如果fx1 类型是G
