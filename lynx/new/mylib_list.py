
import tushare as ts
import pandas as pd
from myobj import Mark, Direction, RawBar, NewBar, FX, CDK, BI
from typing import List
from loguru import logger





# 把dt转换成简单格式
def tostr(dt):
    dt_fmt = "%y%m%d:%H%M"
    date_str = dt.strftime(dt_fmt)
    return date_str


# 检查包含关系
def is_contained(k1, k2) -> int:
    if k1['high'] >= k2['high'] and k1['low'] <= k2['low'] or \
         k1['high'] <= k2['high'] and k1['low'] >= k2['low']:
        return True
    else:
        return False


# 检查存在包含关系的数量
def count_bars(bars:pd.DataFrame) -> int:
    count = 0
    if len(bars) < 2:
        return 0
    for i in range(len(bars)-1):
        k1 = bars.iloc[i]
        k2 = bars.iloc[i+1]
        if is_contained(k1, k2) is not None:
            count += 1
    return count


# 输入一串原始k线，生成无包含关系的k线
def merge_bars(bars: pd.DataFrame) -> pd.DataFrame:
    # 1.若输入空列表或长度不大于2条，返回None
    if not bars or len(bars) <= 2:
        return []

    n = len(bars)
    print('开始处理%d条k线：' % n, end=' ')

    # 2. 从bars头部寻找两条不包含的k线 加入结果列表n_bars
    n_bars = []
    for kline in bars:
        if len(n_bars) < 2:
            n_bars.append(kline)
        else:
            k1, k2 = bars.tail(2)
            if is_contained(k1, k2):
                n_bars.drop(0)

        k3 = kline

        # 如果k3时间比k2大，判断后合并
        if k3.dt > k2.dt:
            has_include, k4 = remove_include(k1, k2, k3)
            if has_include:
                # k2,k3包含，弹出k3,合并k4
                n_bars.pop()
                n_bars.append(k4)
            else:
                # k2，k3不包含，直接合并k4
                n_bars.append(k4)

    print("合并后得到%d条k线" % len(n_bars))
    return n_bars
def remove_include(k1: NewBar, k2: NewBar, k3: RawBar):
    """去除包含关系：输入三根k线，其中k1和k2为没有包含关系的K线，k3为原始K线"""
    if k1.high < k2.high:
        direction = Direction.Up
    elif k1.high > k2.high:
        direction = Direction.Down
    else:
        k4 = NewBar(symbol=k3.symbol, id=k3.id, freq=k3.freq, dt=k3.dt, open=k3.open,
                    close=k3.close, high=k3.high, low=k3.low, vol=k3.vol, elements=[k3])
        return False, k4

    # 判断 k2 和 k3 之间是否存在包含关系，有则处理
    if (k2.high <= k3.high and k2.low >= k3.low) or (k2.high >= k3.high and k2.low <= k3.low):
        if direction == Direction.Up:
            high = max(k2.high, k3.high)
            low = max(k2.low, k3.low)
            dt = k2.dt if k2.high > k3.high else k3.dt
        elif direction == Direction.Down:
            high = min(k2.high, k3.high)
            low = min(k2.low, k3.low)
            dt = k2.dt if k2.low < k3.low else k3.dt
        else:
            raise ValueError

        if k2.open > k3.close:
            open_ = high
            close = low
        else:
            open_ = low
            close = high

        vol = k2.vol + k3.vol
        # 这里有一个隐藏Bug，len(k2.elements) 在一些及其特殊的场景下会有超大的数量，具体问题还没找到；
        # 临时解决方案是直接限定len(k2.elements)<=100
        elements = [x for x in k2.elements[:100] if x.dt != k3.dt] + [k3]
        k4 = NewBar(symbol=k3.symbol, id=k2.id, freq=k2.freq, dt=dt, open=open_,
                    close=close, high=high, low=low, vol=vol, elements=elements)
        return True, k4
    else:
        k4 = NewBar(symbol=k3.symbol, id=k3.id, freq=k3.freq, dt=k3.dt, open=k3.open,
                    close=k3.close, high=k3.high, low=k3.low, vol=k3.vol, elements=[k3])
        return False, k4



def check_fx(k1: NewBar, k2: NewBar, k3: NewBar):
    """查找分型"""
    # Mark.G 顶分，Mark.D 底分；fx 分型的高低点。
    fx = None
    if k1.high < k2.high > k3.high and k1.low < k2.low > k3.low:
        fx = FX(symbol=k1.symbol, dt=k2.dt, mark=Mark.G, high=k2.high,
                high_a=k2.high, low_a=min(k1.low, k2.low),
                low=k2.low, fx=k2.high, elements=[k1, k2, k3])

    if k1.low > k2.low < k3.low and k1.high > k2.high < k3.high:
        fx = FX(symbol=k1.symbol, dt=k2.dt, mark=Mark.D, high=k2.high,
                high_a=max(k1.high, k3.high), low_a=k2.low,
                low=k2.low, fx=k2.low, elements=[k1, k2, k3])

    return fx

def check_fxs(bars: List[NewBar]) -> List[FX]:
    """输入一串无包含关系K线，查找其中所有分型"""
    fxs = []
    for i in range(1, len(bars)-1):
        fx: FX = check_fx(bars[i-1], bars[i], bars[i+1])
        if isinstance(fx, FX):
            fxs.append(fx)
    return fxs


def check_bi(bars: List[NewBar]):
    """输入一串无包含关系K线，查找其中的一笔

    :param bars: 无包含关系K线列表
    :param benchmark: 当下笔能量的比较基准
    :return:
    """
    min_bi_len = 6
    fxs = check_fxs(bars)
    if len(fxs) < 2:
        return None, bars

    fx_a = fxs[0]
    # 笔步骤1 找出两个相反的分型 fx_a fx_b
    try:
        if fxs[0].mark == Mark.D:
            # fx_a是底的话 朝上，求最高的顶分型 fx_b
            direction = Direction.Up
            fxs_b = [x for x in fxs if x.mark == Mark.G and x.dt > fx_a.dt and x.fx > fx_a.fx]
            if not fxs_b:
                return None, bars

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

    logger.info(f"-------笔步骤1a- K线范围-{tostr(bars[0].dt),tostr(bars[-1].dt)}")
    # logger.info(f"-------笔步骤1b- 分型范围{tostr(fx_a.dt), tostr(fx_b.dt)}")
    # 打印 找出的 fx_a和 fx_b
    # logger.info(f"{len(fxs),fx_a.dt, fx_b.dt}")

    # 笔步骤2 计算nk和重叠k
    # bars是合并过的k线，bars_a 计算fx_a左侧--fx_b右侧 范围内的合并k线
    # bars_ar 计算fx_a顶点--fx_b顶点的未合并k线
    # bars_b fx_b左侧开始的合并k线
    bars_a = [x for x in bars if fx_a.elements[0].dt <= x.dt <= fx_b.elements[2].dt]
    bars_ar = []
    for x in bars_a:
        for y in x.elements:
            if fx_a.elements[1].dt <= y.dt <= fx_b.elements[1].dt:
                bars_ar.append(y)
    bars_b = [x for x in bars if x.dt >= fx_b.elements[0].dt]

    # 判断fx_a和fx_b价格区间是否存在包含关系
    ab_include = (fx_a.high > fx_b.high and fx_a.low < fx_b.low) \
                 or (fx_a.high < fx_b.high and fx_a.low > fx_b.low)


    # 判断fx_a的区间和fx_b的区间是否存在包含关系
    # 改写了这个顶分的高点=fx点的high，低点是两外两根k的最低点， 底分的低点=fx点的low， 高点时另外两根k的最高点
    area_include = (fx_a.high_a > fx_b.high_a and fx_a.low_a < fx_b.low_a) \
                   or (fx_a.high_a < fx_b.high_a and fx_a.low_a > fx_b.low_a)

    # area_include = None

    # 计算重叠k线, 从去包含的k线计算
    # has_cdk, cdk_list = check_cdk(bars_a[1:-1])
    # 从原始k线计算,分型顶点不能算，所以
    cdks, bars_c = check_cdk(bars_ar[1:-1])

    # # 判断当前笔的涨跌幅是否超过benchmark的一定比例
    # if benchmark and abs(fx_a.fx - fx_b.fx) > benchmark * envs.get_bi_change_th():
    #     power_enough = True
    # else:
    #     power_enough = False
    power_enough = False

    # 成笔的条件：
    # 1）顶底分型之间没有包含关系；
    # 2) 分型区间之间没有包含关系
    # 3a）笔长度 大于 min_bi_len6
    # 3b) or笔长度 = min_bi_len6,未合并k线>=7
    # 3c）or笔长度 <= min_bi_len6, 笔之间有3K或以上重叠 check_cdk,参数用bars_a去头去尾=bars_a[1:-1],
    # (len(bars_a) <= min_bi_len 这里必须用 <= 不能用 < 不满足大于6k的反面是 <= 否则会报错
    # 或 当前笔的涨跌幅已经够大,不使用
    # flag1 = (len(bars_a) > min_bi_len)
    # flag2 = (len(bars_a) == min_bi_len and len(bars_ar) >= 7)
    # flag3 = (len(bars_a) <= min_bi_len and has_cdk)
    flag_bi = (len(bars_a) > min_bi_len) or \
            (len(bars_a) == min_bi_len and len(bars_ar) >= 7) or \
              (len(bars_a) <= min_bi_len and len(cdks))

    condition = (not area_include) and flag_bi
    # condition = (not ab_include) and (not area_include) and flag_bi
    # condition = (not ab_include) and (len(bars_a) >= min_bi_len)
    # 笔步骤3 条件满足，生成笔对象实例bi，将两端分型中包含的所有分型放入笔的fxs，所有k线放入笔的bars，根据起点分型设置笔方向
    if condition:
    # if (not ab_include) and (len(bars_a) >= min_bi_len or power_enough):
        logger.info(f"笔步骤3-笔范围{tostr(fx_a.dt), tostr(fx_b.dt)}, 笔识别{not ab_include, not area_include, flag_bi, len(bars_a), len(bars_ar), len(cdks)}")
        # logger.info(f"笔步骤3-k线范围{bars[0].dt, bars[-1].dt}, 分型范围{fx_a.dt, fx_b.dt}")
        fxs_ = [x for x in fxs if fx_a.elements[0].dt <= x.dt <= fx_b.elements[2].dt]
        bi = BI(symbol=fx_a.symbol, fx_a=fx_a, fx_b=fx_b, fxs=fxs_, direction=direction, bars=bars_a)

        # 笔步骤3a bi后k线低中低 低于bi的最低点，和 高中高 高于bi的最高点，则笔不成立
        # 为什么会出现：fx_a fx_b 出现后，k还在上涨或下跌，但是未出现新的分型 导致目前的笔失败，但是未来可能会出现新的分型。
        low_ubi = min([x.low for x in bars_b])
        high_ubi = max([x.high for x in bars_b])
        if (bi.direction == Direction.Up and high_ubi > bi.high) \
                or (bi.direction == Direction.Down and low_ubi < bi.low):
            logger.info(f"笔步骤3a 笔被破坏-{tostr(bars[-1].dt)} ,高点：{high_ubi, bi.high}, 低点：{low_ubi, bi.low}")
            return None, bars
        else:
            return bi, bars_b
        # return bi, bars_b
    else:
        return None, bars

def check_cdk(bars: List[RawBar], pre_cdk=None, pre_bar=None, ):
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
                        cdks.append(pre_cdk)
                        # logger.info(f"记录nk重叠{pre_cdk.kcnt, pre_cdk.sdt, pre_cdk.edt}")
                    pre_cdk = None
                    pre_bar = bar

    if len(cdks) > 0:
        bars_ = [x for x in bars if x.dt >= cdks[-1].edt]
    else:
        bars_ = bar

    return cdks, bars_