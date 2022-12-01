# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/10/27 23:17
describe: 使用 ta-lib 构建的信号函数

tas = ta-lib signals 的缩写
"""
from loguru import logger
try:
    import talib as ta
except:
    logger.warning(f"ta-lib 没有正确安装，相关信号函数无法正常执行。"
                   f"请参考安装教程 https://blog.csdn.net/qaz2134560/article/details/98484091")
import numpy as np
from czsc import CZSC, Signal
from czsc.utils import get_sub_elements, fast_slow_cross
from collections import OrderedDict


def update_ma_cache(c: CZSC, ma_type: str, timeperiod: int, **kwargs) -> None:
    """更新均线缓存

    :param c: CZSC对象
    :param ma_type: 均线类型
    :param timeperiod: 计算周期
    :return:
    """
    ma_type_map = {
        'SMA': ta.MA_Type.SMA,
        'EMA': ta.MA_Type.EMA,
        'WMA': ta.MA_Type.WMA,
        'KAMA': ta.MA_Type.KAMA,
        'TEMA': ta.MA_Type.TEMA,
        'DEMA': ta.MA_Type.DEMA,
        'MAMA': ta.MA_Type.MAMA,
        'T3': ta.MA_Type.T3,
        'TRIMA': ta.MA_Type.TRIMA,
    }

    min_count = timeperiod
    cache_key = f"{ma_type.upper()}{timeperiod}"
    last_cache = dict(c.bars_raw[-2].cache) if c.bars_raw[-2].cache else dict()
    if cache_key not in last_cache.keys() or len(c.bars_raw) < min_count + 5:
        # 初始化缓存
        close = np.array([x.close for x in c.bars_raw])
        min_count = 0
    else:
        # 增量更新缓存
        close = np.array([x.close for x in c.bars_raw[-timeperiod - 10:]])

    ma = ta.MA(close, timeperiod=timeperiod, matype=ma_type_map[ma_type.upper()])

    for i in range(1, len(close) - min_count - 5):
        _c = dict(c.bars_raw[-i].cache) if c.bars_raw[-i].cache else dict()
        _c.update({cache_key: ma[-i]})
        c.bars_raw[-i].cache = _c


def update_macd_cache(c: CZSC, **kwargs) -> None:
    """更新MACD缓存

    :param c: CZSC对象
    :return:
    """
    fastperiod = kwargs.get('fastperiod', 12)
    slowperiod = kwargs.get('slowperiod', 26)
    signalperiod = kwargs.get('signalperiod', 9)

    min_count = fastperiod + slowperiod
    cache_key = f"MACD"
    last_cache = dict(c.bars_raw[-2].cache) if c.bars_raw[-2].cache else dict()
    if cache_key not in last_cache.keys() or len(c.bars_raw) < min_count + 30:
        close = np.array([x.close for x in c.bars_raw])
        min_count = 0
    else:
        close = np.array([x.close for x in c.bars_raw[-min_count-30:]])

    dif, dea, macd = ta.MACD(close, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)

    for i in range(1, len(close) - min_count - 10):
        _c = dict(c.bars_raw[-i].cache) if c.bars_raw[-i].cache else dict()
        _c.update({cache_key: {'dif': dif[-i], 'dea': dea[-i], 'macd': macd[-i]}})
        c.bars_raw[-i].cache = _c


def update_boll_cache(c: CZSC, **kwargs) -> None:
    """更新K线的BOLL缓存

    :param c: 交易对象
    :return:
    """
    cache_key = "boll"
    timeperiod = kwargs.get('timeperiod', 20)
    dev_seq = kwargs.get('dev_seq', (1.382, 2, 2.764))

    min_count = timeperiod
    last_cache = dict(c.bars_raw[-2].cache) if c.bars_raw[-2].cache else dict()
    if cache_key not in last_cache.keys() or len(c.bars_raw) < min_count + 30:
        close = np.array([x.close for x in c.bars_raw])
        min_count = 0
    else:
        close = np.array([x.close for x in c.bars_raw[-min_count-30:]])

    u1, m, l1 = ta.BBANDS(close, timeperiod=timeperiod, nbdevup=dev_seq[0], nbdevdn=dev_seq[0], matype=ta.MA_Type.SMA)
    u2, m, l2 = ta.BBANDS(close, timeperiod=timeperiod, nbdevup=dev_seq[1], nbdevdn=dev_seq[1], matype=ta.MA_Type.SMA)
    u3, m, l3 = ta.BBANDS(close, timeperiod=timeperiod, nbdevup=dev_seq[2], nbdevdn=dev_seq[2], matype=ta.MA_Type.SMA)

    for i in range(1, len(close) - min_count - 10):
        _c = dict(c.bars_raw[-i].cache) if c.bars_raw[-i].cache else dict()
        _c.update({cache_key: {"上轨3": u3[-i], "上轨2": u2[-i], "上轨1": u1[-i],
                               "中线": m[-i],
                               "下轨1": l1[-i], "下轨2": l2[-i], "下轨3": l3[-i]}})
        c.bars_raw[-i].cache = _c


# MACD信号计算函数
# ======================================================================================================================

def tas_macd_base_V221028(c: CZSC, di: int = 1, key="macd") -> OrderedDict:
    """MACD|DIF|DEA 多空和方向信号

    **信号逻辑：**

    1. dik 对应的MACD值大于0，多头；反之，空头
    2. dik 的MACD值大于上一个值，向上；反之，向下

    **信号列表：**

    - Signal('30分钟_D1K_MACD_多头_向下_任意_0')
    - Signal('30分钟_D1K_MACD_空头_向下_任意_0')
    - Signal('30分钟_D1K_MACD_多头_向上_任意_0')
    - Signal('30分钟_D1K_MACD_空头_向上_任意_0')

    :param c: CZSC对象
    :param di: 倒数第i根K线
    :param key: 指定使用哪个Key来计算，可选值 [macd, dif, dea]
    :return:
    """
    assert key.lower() in ['macd', 'dif', 'dea']
    k1, k2, k3 = f"{c.freq.value}_D{di}K_{key.upper()}".split('_')

    macd = [x.cache['MACD'][key.lower()] for x in c.bars_raw[-5 - di:]]
    v1 = "多头" if macd[-di] >= 0 else "空头"
    v2 = "向上" if macd[-di] >= macd[-di - 1] else "向下"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value
    return s


def tas_macd_direct_V221106(c: CZSC, di: int = 1) -> OrderedDict:
    """MACD方向；贡献者：马鸣

    **信号逻辑：** 连续三根macd柱子值依次增大，向上；反之，向下

    **信号列表：**

    - Signal('15分钟_D1K_MACD方向_向下_任意_任意_0')
    - Signal('15分钟_D1K_MACD方向_模糊_任意_任意_0')
    - Signal('15分钟_D1K_MACD方向_向上_任意_任意_0')

    :param c: CZSC对象
    :param di: 连续倒3根K线
    :return:
    """
    k1, k2, k3 = f"{c.freq.value}_D{di}K_MACD方向".split("_")
    bars = get_sub_elements(c.bars_raw, di=di, n=3)
    macd = [x.cache['MACD']['macd'] for x in bars]

    if len(macd) != 3:
        v1 = "模糊"
    else:
        # 最近3根 MACD 方向信号
        if macd[-1] > macd[-2] > macd[-3]:
            v1 = "向上"
        elif macd[-1] < macd[-2] < macd[-3]:
            v1 = "向下"
        else:
            v1 = "模糊"

    s = OrderedDict()
    v = Signal(k1=k1, k2=k2, k3=k3, v1=v1)
    s[v.key] = v.value
    return s


def tas_macd_power_V221108(c: CZSC, di: int = 1) -> OrderedDict:
    """MACD强弱

    **信号逻辑：**

    1. 指标超强满足条件：DIF＞DEA＞0；释义：指标超强表示市场价格处于中长期多头趋势中，可能形成凌厉的逼空行情
    2. 指标强势满足条件：DIF-DEA＞0（MACD柱线＞0）释义：指标强势表示市场价格处于中短期多头趋势中，价格涨多跌少，通常是反弹行情
    3. 指标弱势满足条件：DIF-DEA＜0（MACD柱线＜0）释义：指标弱势表示市场价格处于中短期空头趋势中，价格跌多涨少，通常是回调行情
    4. 指标超弱满足条件：DIF＜DEA＜0释义：指标超弱表示市场价格处于中长期空头趋势中，可能形成杀多行情

    **信号列表：**

    - Signal('60分钟_D1K_MACD强弱_超强_任意_任意_0')
    - Signal('60分钟_D1K_MACD强弱_弱势_任意_任意_0')
    - Signal('60分钟_D1K_MACD强弱_超弱_任意_任意_0')
    - Signal('60分钟_D1K_MACD强弱_强势_任意_任意_0')

    :param c: CZSC对象
    :param di: 信号产生在倒数第di根K线
    :return: 信号识别结果
    """
    k1, k2, k3 = f"{c.freq.value}_D{di}K_MACD强弱".split("_")

    v1 = "其他"
    if len(c.bars_raw) > di + 10:
        bar = c.bars_raw[-di]
        dif, dea = bar.cache['MACD']['dif'], bar.cache['MACD']['dea']

        if dif >= dea >= 0:
            v1 = "超强"
        elif dif - dea > 0:
            v1 = "强势"
        elif dif <= dea <= 0:
            v1 = "超弱"
        elif dif - dea < 0:
            v1 = "弱势"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1)
    s[signal.key] = signal.value
    return s


def tas_macd_change_V221105(c: CZSC, di: int = 1, n: int = 55) -> OrderedDict:
    """MACD颜色变化；贡献者：马鸣

    **信号逻辑：** 从dik往前数n根k线对应的macd红绿柱子变换次数

    **信号列表：**

    - Signal('15分钟_D1K55_MACD变色次数_1次_任意_任意_0')
    - Signal('15分钟_D1K55_MACD变色次数_2次_任意_任意_0')
    - Signal('15分钟_D1K55_MACD变色次数_3次_任意_任意_0')
    - Signal('15分钟_D1K55_MACD变色次数_4次_任意_任意_0')
    - Signal('15分钟_D1K55_MACD变色次数_5次_任意_任意_0')
    - Signal('15分钟_D1K55_MACD变色次数_6次_任意_任意_0')
    - Signal('15分钟_D1K55_MACD变色次数_7次_任意_任意_0')
    - Signal('15分钟_D1K55_MACD变色次数_8次_任意_任意_0')
    - Signal('15分钟_D1K55_MACD变色次数_9次_任意_任意_0')

    :param c: czsc对象
    :param di: 倒数第i根K线
    :param n: 从dik往前数n根k线
    :return:
    """
    k1, k2, k3 = f"{c.freq.value}_D{di}K{n}_MACD变色次数".split('_')

    bars = get_sub_elements(c.bars_raw, di=di, n=n)
    dif = [x.cache['MACD']['dif'] for x in bars]
    dea = [x.cache['MACD']['dea'] for x in bars]

    cross = fast_slow_cross(dif, dea)
    # 过滤低级别信号抖动造成的金叉死叉(这个参数根据自身需要进行修改）
    re_cross = [i for i in cross if i['距离'] >= 2]

    if len(re_cross) == 0:
        num = 0
    else:
        cross_ = []
        for i in range(0, len(re_cross)):
            if len(cross_) >= 1 and re_cross[i]['类型'] == re_cross[i - 1]['类型']:
                # 不将上一个元素加入cross_
                del cross_[-1]

                # 我这里只重新计算了面积、快慢线的高低点，其他需要重新计算的参数各位可自行编写
                re_cross[i]['面积'] = re_cross[i - 1]['面积'] + re_cross[i]['面积']

                re_cross[i]['快线高点'] = max(re_cross[i - 1]['快线高点'], re_cross[i]['快线高点'])
                re_cross[i]['快线低点'] = min(re_cross[i - 1]['快线低点'], re_cross[i]['快线低点'])

                re_cross[i]['慢线高点'] = max(re_cross[i - 1]['慢线高点'], re_cross[i]['慢线高点'])
                re_cross[i]['慢线低点'] = min(re_cross[i - 1]['慢线低点'], re_cross[i]['慢线低点'])

                cross_.append(re_cross[i])
            else:
                cross_.append(re_cross[i])
        num = len(cross_)

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=f"{num}次")
    s[signal.key] = signal.value
    return s


# MA信号计算函数
# ======================================================================================================================

def tas_ma_base_V221101(c: CZSC, di: int = 1, key="SMA5") -> OrderedDict:
    """MA 多空和方向信号

    **信号逻辑：**

    1. close > ma，多头；反之，空头
    2. ma[-1] > ma[-2]，向上；反之，向下

    **信号列表：**

    - Signal('15分钟_D1K_SMA5_空头_向下_任意_0')
    - Signal('15分钟_D1K_SMA5_多头_向下_任意_0')
    - Signal('15分钟_D1K_SMA5_多头_向上_任意_0')
    - Signal('15分钟_D1K_SMA5_空头_向上_任意_0')

    :param c: CZSC对象
    :param di: 信号计算截止倒数第i根K线
    :param key: 指定使用哪个Key来计算，必须是 `update_ma_cache` 中已经缓存的 key
    :return:
    """
    k1, k2, k3 = f"{c.freq.value}_D{di}K_{key.upper()}".split('_')
    bars = get_sub_elements(c.bars_raw, di=di, n=3)
    v1 = "多头" if bars[-1].close >= bars[-1].cache[key] else "空头"
    v2 = "向上" if bars[-1].cache[key] >= bars[-2].cache[key] else "向下"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value
    return s


# BOLL信号计算函数
# ======================================================================================================================


def tas_boll_power_V221112(c: CZSC, di: int = 1):
    """BOLL指标强弱

    **信号逻辑：**

    1. close大于中线，多头；反之，空头
    2. close超过轨3，超强，以此类推

    **信号列表：**

    - Signal('15分钟_D1K_BOLL强弱_空头_强势_任意_0')
    - Signal('15分钟_D1K_BOLL强弱_空头_弱势_任意_0')
    - Signal('15分钟_D1K_BOLL强弱_多头_强势_任意_0')
    - Signal('15分钟_D1K_BOLL强弱_多头_弱势_任意_0')
    - Signal('15分钟_D1K_BOLL强弱_空头_超强_任意_0')
    - Signal('15分钟_D1K_BOLL强弱_空头_极强_任意_0')
    - Signal('15分钟_D1K_BOLL强弱_多头_超强_任意_0')
    - Signal('15分钟_D1K_BOLL强弱_多头_极强_任意_0')

    :param c: CZSC对象
    :param di: 信号计算截止倒数第i根K线
    :return: s
    """
    k1, k2, k3 = f"{c.freq.value}_D{di}K_BOLL强弱".split("_")

    if len(c.bars_raw) < di + 20:
        v1, v2 = '其他', '其他'

    else:
        last = c.bars_raw[-di]
        cache = last.cache['boll']

        latest_c = last.close
        m = cache['中线']
        u3, u2, u1 = cache['上轨3'], cache['上轨2'], cache['上轨1']
        l3, l2, l1 = cache['下轨3'], cache['下轨2'], cache['下轨1']

        v1 = "多头" if latest_c >= m else "空头"

        if latest_c >= u3 or latest_c <= l3:
            v2 = "极强"
        elif latest_c >= u2 or latest_c <= l2:
            v2 = "超强"
        elif latest_c >= u1 or latest_c <= l1:
            v2 = "强势"
        else:
            v2 = "弱势"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value
    return s


def tas_boll_bc_V221118(c: CZSC, di=1, n=3, m=10, line=3):
    """BOLL背驰辅助

    **信号逻辑：**

    近n个最低价创近m个周期新低，近m个周期跌破下轨，近n个周期不破下轨，这是BOLL一买（底部背驰）信号，顶部背驰反之。

    **信号列表：**

    - Signal('60分钟_D1N3M10L2_BOLL背驰_一卖_任意_任意_0')
    - Signal('60分钟_D1N3M10L2_BOLL背驰_一买_任意_任意_0')

    :param c: CZSC对象
    :param di: 倒数第di根K线
    :param n: 近n个周期
    :param m: 近m个周期
    :param line: 选第几个上下轨
    :return:
    """
    k1, k2, k3 = f"{c.freq.value}_D{di}N{n}M{m}L{line}_BOLL背驰".split('_')

    bn = get_sub_elements(c.bars_raw, di=di, n=n)
    bm = get_sub_elements(c.bars_raw, di=di, n=m)

    d_c1 = min([x.low for x in bn]) <= min([x.low for x in bm])
    d_c2 = sum([x.close < x.cache['boll'][f'下轨{line}'] for x in bm]) > 1
    d_c3 = sum([x.close < x.cache['boll'][f'下轨{line}'] for x in bn]) == 0

    g_c1 = max([x.high for x in bn]) == max([x.high for x in bm])
    g_c2 = sum([x.close > x.cache['boll'][f'上轨{line}'] for x in bm]) > 1
    g_c3 = sum([x.close > x.cache['boll'][f'上轨{line}'] for x in bn]) == 0

    if d_c1 and d_c2 and d_c3:
        v1 = "一买"
    elif g_c1 and g_c2 and g_c3:
        v1 = "一卖"
    else:
        v1 = "其他"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1)
    s[signal.key] = signal.value
    return s

def tas_dea_cross_V221106(c: CZSC, di=55) -> OrderedDict:
    """dea穿过0轴次数

    信号逻辑：
    连续三根macd柱子值依次增大，向上；反之，向下

    信号列表：
    - Signal('15分钟_近55根K线DEA_上穿0轴_1次_任意_任意_0')
    - Signal('15分钟_近55根K线DEA_处于0轴以上_是_任意_任意_0')
    - Signal('15分钟_近55根K线DEA_处于0轴以下_是_任意_任意_0')

    :param c: CZSC对象
    :param di: 连续倒3根K线
    :return:
    """

    s = OrderedDict()

    default_signals = [
        Signal(k1=str(c.freq.value), k2=f"近{di}根K线DEA", k3="上穿0轴", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(c.freq.value), k2=f"近{di}根K线DEA", k3="处于0轴以上", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(c.freq.value), k2=f"近{di}根K线DEA", k3="处于0轴以下", v1="其他", v2='其他', v3='其他')
    ]

    for signal in default_signals:
        s[signal.key] = signal.value

    dea = [x.cache['MACD']['dea'] for x in c.bars_raw[-di:]]

    # dea上穿0轴
    up = down_cross_count([0 for i in range(len(dea))], dea)
    down = down_cross_count(dea, [0 for i in range(len(dea))])

    # 上穿一次0轴，最后一根K线的DEA在0轴上，倒数第5根K线DEA在0轴下
    if up == 1 and down == 0 and dea[-1] > 0:
        v = Signal(k1=str(c.freq.value), k2=f"近{di}根K线DEA", k3="上穿0轴", v1=f"1次")
        s[v.key] = v.value

    # 上穿一次或始终处于0轴上方，最近X根K线macd均处于0轴上方
    if up == down == 0 and dea[-di] > 0:
        v = Signal(k1=str(c.freq.value), k2=f"近{di}根K线DEA", k3="处于0轴以上", v1=f"是")
        s[v.key] = v.value
    elif up == down == 0 and dea[-di] < 0:
        v = Signal(k1=str(c.freq.value), k2=f"近{di}根K线DEA", k3="处于0轴以下", v1=f"是")
        s[v.key] = v.value

    return s

def tas_dif_zero_V221106(c: CZSC, di=55) -> OrderedDict:
    """dif回抽0轴

    信号逻辑：
    1.首先在基于di根k线为一段向上趋势；
    2.其次连续di根k线形成的dif最低点在 +—dif最大值0.2倍之间，在此期间判断为上涨过程中回抽0轴

    信号列表：
    - Signal('15分钟_近55根K线DIF_回抽0轴_否_任意_任意_0')
    - Signal('15分钟_近55根K线DIF_回抽0轴_是_任意_任意_0')

    :param c: CZSC对象
    :param di: 连续倒di根K线
    :return:
    """
    dif = [x.cache['MACD']['dif'] for x in c.bars_raw[-di:]]

    s = OrderedDict()

    # 近di根K线的dif的最小值，在正负0.2*dif最大值区间内，即回抽0轴
    if - max(dif) * 0.2 < min(dif) < max(dif) * 0.2:
        v = Signal(k1=str(c.freq.value), k2=f"近{di}根K线DIF", k3="回抽0轴", v1=f"是")
    else:
        v = Signal(k1=str(c.freq.value), k2=f"近{di}根K线DIF", k3="回抽0轴", v1=f"否")
    s[v.key] = v.value
    return s

def macd_zs_v221106(c: CZSC, di=55) -> OrderedDict:
    """单纯通过价格判断股价突破中枢

    信号逻辑：
    1.划定[-di:-13]区间为中枢区间，取其高点；
    2.取倒13根K线的最高点，此笔为中枢突破；
    3.取倒3笔的低点，判断该点位与中枢的相对位置

    信号列表：
    - Signal('15分钟_K线价格_冲高回落_中枢之内_任意_任意_0')
    - Signal('15分钟_K线价格_冲高回落_中枢之上_任意_任意_0')

    :param c: CZSC对象
    :param di: 连续倒di根K线
    :return:
    """
    s = OrderedDict()

    high_zs = max([x.high for x in c.bars_raw][-di:-13])
    high_last_bi = max([x.high for x in c.bars_raw][-13:])
    low_last_bi = min([x.low for x in c.bars_raw][-3:])

    if high_zs < low_last_bi < high_last_bi < high_zs * 1.1:
        v = Signal(k1=str(c.freq.value), k2='K线价格', k3="冲高回落", v1="中枢之上")
        s[v.key] = v.value
    elif high_zs > low_last_bi:
        v = Signal(k1=str(c.freq.value), k2='K线价格', k3="冲高回落", v1="中枢之内")
        s[v.key] = v.value
    else:
        v = Signal(k1=str(c.freq.value), k2='K线价格', k3="冲高回落", v1="其他")
        s[v.key] = v.value

    return s


from czsc.signals.utils import check_cross_info


# 计算倒di根k线Macd面积
# macd柱子面积背驰
def tas_macd_area_compare_V221106(c: CZSC, di: int = 55) -> OrderedDict:
    """MACD柱子面积背驰

    信号逻辑：
    计算最近di根K线周期中，两次相邻macd柱子面积背驰比较

    信号列表：
    - Signal('15分钟_绿柱子_背驰_绿柱子_否_任意_0')
    - Signal('15分钟_绿柱子_背驰_绿柱子_是_任意_0')
    - Signal('15分钟_红柱子_背驰_红柱子_否_任意_0')
    - Signal('15分钟_红柱子_背驰_红柱子_是_任意_0')

    :param c: czsc对象
    :param di:最近di跟K线
    :return:
    """

    k1, k2, k3 = f"{c.freq.value}_绿柱子_背驰".split('_')
    m1, m2, m3 = f"{c.freq.value}_红柱子_背驰".split('_')

    dif = [x.cache['MACD']['dif'] for x in c.bars_raw[-di:]]
    dea = [x.cache['MACD']['dea'] for x in c.bars_raw[-di:]]

    cross = check_cross_info(dif, dea)

    # 过滤低级别信号抖动造成的金叉死叉(这个参数根据自身需要进行修改）
    re_cross = [i for i in cross if i['距离'] >= 2]
    cross_ = []

    if len(re_cross) == 0:
        pass
    else:
        for i in range(0, len(re_cross)):
            if len(cross_) >= 1 and re_cross[i]['类型'] == re_cross[i - 1]['类型']:
                # 不将上一个元素加入cross_
                del cross_[-1]

                # 我这里只重新计算了面积、快慢线的高低点，其他需要重新计算的参数各位可自行编写
                re_cross[i]['面积'] = re_cross[i - 1]['面积'] + re_cross[i]['面积']

                re_cross[i]['快线高点'] = max(re_cross[i - 1]['快线高点'], re_cross[i]['快线高点'])
                re_cross[i]['快线低点'] = min(re_cross[i - 1]['快线低点'], re_cross[i]['快线低点'])

                re_cross[i]['慢线高点'] = max(re_cross[i - 1]['慢线高点'], re_cross[i]['慢线高点'])
                re_cross[i]['慢线低点'] = min(re_cross[i - 1]['慢线低点'], re_cross[i]['慢线低点'])

                cross_.append(re_cross[i])
            else:
                cross_.append(re_cross[i])

    # 金叉判断基于剔除抖动的cross_列表
    gold_x = [i for i in cross_ if i['类型'] == '金叉']
    die_x = [i for i in cross_ if i['类型'] == '死叉']

    s = OrderedDict()
    # 最后一次金叉的面积 < 倒数第二次金叉的面积
    if len(gold_x) >= 2 and gold_x[-1]['面积'] < gold_x[-2]['面积']:
        v1 = '绿柱子'
        v2 = '是'
    else:
        v1 = '绿柱子'
        v2 = '否'
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)
    s[signal.key] = signal.value

    if len(die_x) >= 2 and die_x[-1]['面积'] < die_x[-2]['面积']:
        w1 = '红柱子'
        w2 = '是'
    else:
        w1 = '红柱子'
        w2 = '否'
    signal = Signal(k1=m1, k2=m2, k3=m3, v1=w1, v2=w2)
    s[signal.key] = signal.value

    return s