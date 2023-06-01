
import tushare as ts
import pandas as pd
import numpy as np

from czsc.data.jq import dt_fmt
from myobj import Mark, Direction, RawBar, NewBar, FX, CDK, BI
from typing import List
from loguru import logger

dt_fmt = "%Y-%m-%d %H:%M:%S"
date_fmt = "%Y-%m-%d"


logger.level("INFO")


# 把dt转换成简单格式
def tostr(dt):
    short_fmt = "%y-%m%d-%H%M"
    # dt = pd.to_datetime(dt)
    date_str = dt.strftime(short_fmt)
    return date_str

def format_bars(df, freq):
    # 转换成czsc统一的格式
    # df = df.rename(columns={'code': 'symbol', 'date': 'dt', 'volume': 'vol', 'turnoverratio': 'turno', })
    df['symbol'] = df['code']
    df['freq'] = freq
    df['date'] = pd.to_datetime(df['date'], format=dt_fmt)
    df['dt'] = df['date']
    df['vol'] = df['volume']
    if 'turnoverratio' in df:
        df['turno'] = df['turnoverratio']


    # df['elements'] = np.nan
    df['id'] = df.reset_index().index
    # print(df.tail(1))
    return df
def get_bars(symbol, freq):
    logger.info(f"获取{symbol,freq}的k线开始:")
    # df = ts.get_k_data(code='688111', ktype='5', autype='qfq', start=None, end=None)
    df = ts.get_k_data(code=symbol, ktype=freq, index=False, autype='qfq')  #查股票
    # df = ts.get_k_data(code=symbol, index=True, ktype=freq, autype='qfq')   # 查指数

    print(df.columns)
    # 获取数据格式['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'turnoverratio', 'code']
    df = format_bars(df[-200:], freq)
    logger.info(f"得到{0 if df.empty else len(df)}根k线。")
    return df


# 检查包含关系
def is_contained(k1:pd.DataFrame, k2:pd.DataFrame) -> bool:
    # if k1.isna().any() or k2.isna().any():
    #     return False
    if k1['high'] >= k2['high'] and k1['low'] <= k2['low'] or \
         k1['high'] <= k2['high'] and k1['low'] >= k2['low']:
        return True
    else:
        return False


# 提供一组处理过的k线，检查是否处理干净，还存在包含关系的数量。
def count_bars(bars: pd.DataFrame) -> int:
    count = 0
    if len(bars) < 2:
        return 0
    for i in range(len(bars)-1):
        k1 = bars.iloc[i]
        k2 = bars.iloc[i+1]
        if is_contained(k1, k2):
            count += 1
    return count


# 输入一串原始k线，生成无包含关系的k线
def merge_bars(df: pd.DataFrame)->pd.DataFrame:
    # 1.若输入空DataFrame或长度不大于2条，返回None
    if df.empty or len(df) <= 2:
        return pd.DataFrame()

    # n = len(df)
    print(f"开始合并k线,输入{len(df)}条原始k线:", end=' ')

    # 2. 从df头部寻找两条不包含的k线 加入结果列表n_df
    n_df = pd.DataFrame(columns=df.columns)
    for i, row in df.iterrows():
        # logger.info(f"打印df第{i}行:{row.to_dict()}")
        if len(n_df) < 2:
            # pd.append()已经废弃，要改成pd.concat()， 再用row.to_frame().T把Series对象转换成DataFrame对象
            n_df = pd.concat([n_df, row.to_frame().T], ignore_index=True)
            # logger.info(f"打印n_df:{len(n_df), n_df['dt'].to_list()}")
        else:
            k1, k2 = n_df.iloc[-2], n_df.iloc[-1]
            # 如果k1,k2包含，则ndf从头部去掉一行（还是清空n_df?)；
            # 正常应该不执行k3后面的函数，所以在else执行后面的预计
            if is_contained(k1, k2):
                n_df = n_df.iloc[1:]
                # n_df.drop(n_df.index, inplace=True)
                # logger.info(f"有包含关系：打印n_df:{len(n_df), k1['dt'], k2['dt'], n_df['dt'].to_list()}")
                # logger.info(f"有包含关系：打印n_df:{len(n_df)}")
            else:
                # 当len(n_df)>=2 且 k1,k2不包含时才会进行合并k线操作（nan是也算不包含?)
                # 发现 k3['dt'] row['dt']的类型都是string，应该是get_bars函数没有处理成日期
                k3 = row
                # 如果k3时间比k2大，判断后合并
                # logger.info(f"打印k1, k2, k3：{k1['dt'],k2['dt'],k3['dt']}")
                # logger.info(f"k3.dt的类型:{type(k3['dt']),type(row['dt'])}")
                if k3['dt'] > k2['dt']:
                    has_include, k4 = remove_include(k1, k2, k3)
                    if has_include: # k2,k3包含，n_df弹出k2,合并k4
                        n_df = n_df.iloc[:-1]
                        n_df = pd.concat([n_df, k4], ignore_index=True)
                    else:   # k2,k3不包含，n_df合并k3
                        n_df = pd.concat([n_df, k3.to_frame().T], ignore_index=True)

    print("合并后得到%d条k线" % len(n_df))
    return n_df


# 给定3根k线，返回处理过k2,k3包含关系的k
def remove_include(k1, k2, k3):
    # 1.若输入为空，返回False和空DataFrame
    if k1.empty or k2.empty or k3.empty:
        return False, pd.DataFrame()

    # 2. 判断k1和k2的最高价，判断方向
    if k1['high'] < k2['high']:
        direction = Direction.Up
    elif k1['high'] > k2['high']:
        direction = Direction.Down
    else:
        # k1和k2高相当，不能判断走势方向，但是说明包含
        k4 = k3.copy()
        return False, k4

    #3. 判断k2和k3之间是否存在包含关系，有则处理
    if (k2['high'] <= k3['high'] and k2['low'] >= k3['low']) \
            or (k2['high'] >= k3['high'] and k2['low'] <= k3['low']):
        if direction == Direction.Up:
            high = max(k2['high'], k3['high'])
            low = max(k2['low'], k3['low'])
            dt = k2['dt'] if k2['high'] > k3['high'] else k3['dt']
        elif direction == Direction.Down:
            high = min(k2['high'], k3['high'])
            low = min(k2['low'], k3['low'])
            dt = k2['dt'] if k2['low'] < k3['low'] else k3['dt']

        if k2['open'] > k3['close']:
            open_ = high
            close = low
        else:
            open_ = low
            close = high

        # vol = k2['vol'] + k3['vol']
        vol = k2['vol'] + k3['vol']
        # elements = [x for x in k2['elements'] if x['dt'] != k3['dt']] + [ k3 ]
        # elements = Nones
        # k4 = {'symbol': k3['symbol'], 'id': k2['id'], 'freq': k2['freq'], 'dt': dt,
        #       'open': open_, 'close': close, 'high': high, 'low': low, 'vol': vol, 'elements': elements}
        k4 = {'symbol': k3['symbol'], 'id': k2['id'], 'freq': k2['freq'], 'dt': dt,
              'open': open_, 'close': close, 'high': high, 'low': low, 'vol': vol}
        return True, pd.DataFrame([k4])
    else:
        k4 = k3.copy()
        return False, k4


def check_fx(k1, k2, k3):
    """查找分型"""
    # Mark.G 顶分，Mark.D 底分；fx 分型的高低点。
    fx = None
    if k1['high'] < k2['high'] > k3['high'] and k1['low'] < k2['low'] > k3['low']:
        fx = FX(symbol=k1['symbol'], dt=k2['dt'], mark=Mark.G, high=k2['high'],
                low=min(k1['low'], k2['low']), fx=k2['high'], elements=[k1, k2, k3])

    if k1['low'] > k2['low'] < k3['low'] and k1['high'] > k2['high'] < k3['high']:
        fx = FX(symbol=k1['symbol'], dt=k2['dt'], mark=Mark.D, high=max(k1['high'], k3['high']),
                low=k2['low'], fx=k2['low'], elements=[k1, k2, k3])

    # if fx:
    #     logger.info(f"fx的dt类型{type(k2['dt']) ,type(k2['high'])}")

    return fx

def check_fxs(bars) -> List[FX]:
    """输入一串无包含关系K线，查找其中所有分型"""
    print(f"开始查找分型，输入{len(bars)}根已合并k线:", end=' ')
    fxs = []
    for i in range(1, len(bars)-1):
        fx: FX = check_fx(bars.iloc[i-1], bars.iloc[i], bars.iloc[i+1])
        if isinstance(fx, FX):
            fxs.append(fx)

    print(f"找到{len(fxs)}个分型:")
    return fxs


def check_bi(bars, fxs):
    # 一笔条件，两个分型点之间的最小k线数
    min_bi_len = 4
def check_bi(bars, bars_raw):
    """输入一串无包含关系K线，查找其中的一笔

    :param bars: 无包含关系K线列表
    :param benchmark: 当下笔能量的比较基准
    :return:
    """
    # 一笔条件，两个分型点之间的最小k线数
    min_bi_len = 4
    fxs = check_fxs(bars)
    if len(fxs) < 2:
        return None, bars

    fx_a = fxs[0]
    # 笔步骤1 找出两个相反的分型 第一个分型fx_a  反向极值分型fx_b #用第一个分型是为了好递归
    try:
        if fxs[0].mark == Mark.D:
            # fx_a是底的话 朝上，找出所有fx点大于fx_a的fx点的顶分型fxs_b的集合，找不到返回None
            direction = Direction.Up
            fxs_b = [x for x in fxs if x.mark == Mark.G and x.dt > fx_a.dt and x.fx > fx_a.fx]
            if not fxs_b:
                return None, bars

            # 在顶分型集合fxs_b中找到最高的fx_b
            fx_b = fxs_b[0]
            for fx in fxs_b[1:]:
                if fx.high >= fx_b.high:
                    fx_b = fx

        elif fxs[0].mark == Mark.G:
            # fx_a是顶的话 朝下，求最低的底分型 fx_b
            direction = Direction.Down
            fxs_b = [x for x in fxs if x.mark == Mark.D and x.dt > fx_a.dt and x.fx < fx_a.fx]
            if not fxs_b:
                return None, bars

            fx_b = fxs_b[0]
            for fx in fxs_b[1:]:
                if fx.low <= fx_b.low:
                    fx_b = fx
        else:
            raise ValueError
    except:
        logger.exception("笔识别错误")
        return None, bars

    # logger.info(f"-------笔步骤1a- K线范围-{tostr(bars[0].dt),tostr(bars[-1].dt)}")

    # 打印 找出的 fx_a和 fx_b
    # logger.info(f"{len(fxs),fx_a.dt, fx_b.dt}")
    logger.info(f"-------笔步骤1b- 分型范围{tostr(fx_a.dt), tostr(fx_b.dt)}")

    # 笔步骤2 计算nk和重叠k
    # bars是合并过的k线，bars_a 计算fx_a左侧--fx_b右侧 范围内的合并k线
    # bars_ar 计算fx_a顶点--fx_b顶点的未合并k线
    # bars_b fx_b左侧开始的合并k线
    # bars_a = [x for x in bars if fx_a.elements[0].dt <= x.dt <= fx_b.elements[2].dt]
    # fx_a.elements[1] 是一个df的行，所以不能用.dt 要用['dt']
    # bars_a 现在的写法是列表，要用df的写法
    print(type(bars.iloc[0]['dt']), type(fx_a.elements[1]['dt']), type(fx_b.elements[1]['dt']))
    # for x in bars:
    #     if fx_a.elements[1]['dt'] <= x['dt'] <= fx_b.elements[1]['dt']:
    #         bars_a = pd.concat([bars_a, x.to_frame().T], ignore_index=True)
    bars_a = bars[bars['dt'].between(fx_a.elements[1]['dt'], fx_b.elements[1]['dt'])]
    bars_ar = bars_raw[bars_raw['dt'].between(fx_a.elements[1]['dt'], fx_b.elements[1]['dt'])]
    # bars_a = bars[fx_a.elements[1]['dt'] <= bars['dt'] <= fx_b.elements[1]['dt']]
    # bars_ar = bars_raw[fx_a.elements[1]['dt'] <= bars_raw['dt'] <= fx_b.elements[1]['dt']]
    bars_b = bars[bars['dt'] >= fx_b.elements[0]['dt']]
    # bars_a = [x for x in bars if fx_a.elements[1]['dt'] <= x['dt'] <= fx_b.elements[1]['dt']]
    # bars_ar = [x for x in bars_raw if fx_a.elements[1]['dt'] <= x['dt'] <= fx_b.elements[1]['dt']]
    # bars_b = [x for x in bars if x['dt'] >= fx_b.elements[0]['dt']]

    # 判断fx_a和fx_b价格区间是否存在包含关系
    # ab_include = (fx_a.high > fx_b.high and fx_a.low < fx_b.low) \
    #              or (fx_a.high < fx_b.high and fx_a.low > fx_b.low)
    not_include = (fx_a.high > fx_b.high and fx_a.low > fx_b.low) \
                 or (fx_a.high < fx_b.high and fx_a.low < fx_b.low)


    # 计算重叠k线, 从去包含的k线计算
    # has_cdk, cdk_list = check_cdk(bars_a[1:-1])
    # 从原始k线计算,分型顶点不能算，所以
    # cdks, bars_c = check_cdk(bars_ar[1:-1])
    # cdks给默认值，绕开check_cdk函数
    cdks = []

    # 成笔的条件：
    # 1）顶底分型之间没有包含关系；
    # 2) 分型区间之间没有包含关系
    # 3a）笔长度 大于 min_bi_len
    # 3b) or笔长度 = min_bi_len6,未合并k线>=7
    # 3c）or笔长度 <= min_bi_len6, 笔之间有3K或以上重叠 check_cdk,参数用bars_a去头去尾=bars_a[1:-1],
    # (len(bars_a) <= min_bi_len 这里必须用 <= 不能用 < 不满足大于6k的反面是 <= 否则会报错
    flag_bi = (len(bars_a) > min_bi_len) or \
            (len(bars_a) == min_bi_len and len(bars_ar) >= 5) or \
              (len(bars_a) <= min_bi_len and len(cdks))

    # condition = (not ab_include) and flag_bi
    condition = not_include and flag_bi
    # condition = (not ab_include) and (len(bars_a) >= min_bi_len)
    # 笔步骤3 条件满足，生成笔对象实例bi，将两端分型中包含的所有分型放入笔的fxs，所有k线放入笔的bars，根据起点分型设置笔方向
    if condition:
    # if (not ab_include) and (len(bars_a) >= min_bi_len or power_enough):
        logger.info(f"笔步骤3-笔范围{tostr(fx_a.dt), tostr(fx_b.dt)}, 笔识别{not_include, flag_bi, len(bars_a), len(bars_ar), len(cdks)}")
        # logger.info(f"笔步骤3-k线范围{bars[0].dt, bars[-1].dt}, 分型范围{fx_a.dt, fx_b.dt}")
        fxs_ = [x for x in fxs if fx_a.elements[0]['dt'] <= x.dt <= fx_b.elements[2]['dt']]
        bi = BI(symbol=fx_a.symbol, fx_a=fx_a, fx_b=fx_b, fxs=fxs_, direction=direction, bars=bars_a)

        # 笔步骤3a bi后k线低中低 低于bi的最低点，和 高中高 高于bi的最高点，则笔不成立
        # 为什么会出现：fx_a fx_b 出现后，k还在上涨或下跌，但是未出现新的分型 导致目前的笔失败，但是未来可能会出现新的分型。
        # print(type(bars_b.iloc[0]['low']))
        # low_ubi = min([x['low'] for x in bars_b])
        # high_ubi = max([x['high'] for x in bars_b])
        low_ubi = bars_b['low'].min()
        high_ubi = bars_b['high'].max()

        if (bi.direction == Direction.Up and high_ubi > bi.high) \
                or (bi.direction == Direction.Down and low_ubi < bi.low):
            logger.info(f"笔步骤3a 笔被破坏-{tostr(bars[-1].dt)} ,高点：{high_ubi, bi.high}, 低点：{low_ubi, bi.low}")
            return None, bars
        else:
            return bi, bars_b
        # return bi, bars_b
    else:
        return None, bars

def check_cdk(bars, pre_cdk=None, pre_bar=None, ):
    cdks = []
    # pre_bar = None
    # pre_cdk = None

    for bar in bars:
        if not pre_bar:  # 第一个bar的时候pre_bar为空，向下取
            pre_bar = bar
        else:
            # if isinstance(pre, RawBar):   # 这个无法判断，不知道原因；如果pre是RawBar，说明重叠已经断开，或者还没有重叠
            if not pre_cdk:  # pre_bar有值，pre_cdk 没有值，循环比较2k，找出重叠的k，写入 pre_cdk
                minh = min(pre_bar.high, bar.high)
                maxl = max(pre_bar.low, bar.low)
                if minh >= maxl:
                    pre_cdk = CDK(sdt=pre_bar.dt, edt=bar.dt, high=minh, low=maxl, kcnt=2, elements=(pre_bar, bar))
                    # logger.info(f"发现2k重叠{pre_cdk.kcnt,pre_cdk.sdt,pre_cdk.edt}")
                else:
                    pre_bar = bar
            # elif isinstance(pre, CDK):    # 这个无法判断，不知道原因 如果pre是CDK，说明已经有重叠了，重叠和bar比较
            elif pre_cdk:  # pre_cdk 有值，循环比较pre_cdk和bar，找出重叠的k，更新 pre_cdk
                minh = min(pre_cdk.high, bar.high)
                maxl = max(pre_cdk.low, bar.low)
                if minh >= maxl:
                    pre_cdk.edt = bar.dt
                    pre_cdk.high = minh
                    pre_cdk.low = maxl
                    pre_cdk.kcnt += 1
                    pre_cdk.elements += (bar,)
                    # logger.info(f"发现nk重叠{pre_cdk.kcnt, pre_cdk.sdt, pre_cdk.edt}")
                else:  # 如果找不出重叠，且kcnt>=3 pre_cdk加入列表； 然后清空pre_cdk，赋值pre_bar 寻找新的重叠
                    if pre_cdk.kcnt >= 3:
                        cdks.concat(pre_cdk)
                        # logger.info(f"记录nk重叠{pre_cdk.kcnt, pre_cdk.sdt, pre_cdk.edt}")
                    pre_cdk = None
                    pre_bar = bar

    if len(cdks) > 0:
        bars_ = [x for x in bars if x.dt >= cdks[-1].edt]
    else:
        bars_ = bar

    return cdks, bars_