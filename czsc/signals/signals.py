# coding: utf-8
import numpy as np
from collections import OrderedDict

from czsc import analyze
from czsc import CZSC, Freq, Signal
from ..objects import Direction, Signal
from ..enum import Freq
from ..utils.ta import MACD, SMA
from ..signals.utils import kdj_gold_cross
from ..signals import utils
from .bxt import get_s_like_bs, get_s_d0_bi, get_s_bi_status, get_s_di_bi, get_s_base_xt, get_s_three_bi
from .ta import get_s_single_k, get_s_three_k, get_s_sma, get_s_macd


def get_default_signals(c: analyze.CZSC) -> OrderedDict:
    """在 CZSC 对象上计算信号，这个是标准函数，主要用于研究。

    实盘时可以按照自己的需要自定义计算哪些信号。

    :param c: CZSC 对象
    :return: 信号字典
    """
    s = OrderedDict({"symbol": c.symbol, "dt": c.bars_raw[-1].dt, "close": c.bars_raw[-1].close})

    s.update(get_s_d0_bi(c))
    s.update(get_s_three_k(c, 1))
    s.update(get_s_di_bi(c, 1))
    s.update(get_s_macd(c, 1))
    s.update(get_s_single_k(c, 1))
    s.update(get_s_bi_status(c))

    for di in range(1, 8):
        s.update(get_s_three_bi(c, di))

    for di in range(1, 8):
        s.update(get_s_base_xt(c, di))

    for di in range(1, 8):
        s.update(get_s_like_bs(c, di))
    return s


def get_selector_signals(c: analyze.CZSC) -> OrderedDict:
    """在 CZSC 对象上计算选股信号

    :param c: CZSC 对象
    :return: 信号字典
    """
    freq: Freq = c.freq
    s = OrderedDict({"symbol": c.symbol, "dt": c.bars_raw[-1].dt, "close": c.bars_raw[-1].close})

    s.update(get_s_three_k(c, 1))
    s.update(get_s_bi_status(c))

    for di in range(1, 3):
        s.update(get_s_three_bi(c, di))

    for di in range(1, 3):
        s.update(get_s_base_xt(c, di))

    for di in range(1, 3):
        s.update(get_s_like_bs(c, di))

    default_signals = [
        # 以下是技术指标相关信号
        Signal(k1=str(freq.value), k2="成交量", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(freq.value), k2="MA5状态", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(freq.value), k2="KDJ状态", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(freq.value), k2="MACD状态", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(freq.value), k2="倒0笔", k3="潜在三买", v1="其他", v2='其他', v3='其他'),
    ]
    for signal in default_signals:
        s[signal.key] = signal.value

    if not c.bi_list:
        return s

    if len(c.bars_raw) > 30 and c.freq == Freq.D:
        last_vols = [k_.open * k_.vol for k_ in c.bars_raw[-10:]]
        if sum(last_vols) > 15e8 and min(last_vols) > 1e7:
            v = Signal(k1=str(freq.value), k2="成交量", v1="近10个交易日累计成交金额大于15亿", v2='近10个交易日最低成交额大于1亿')
            s[v.key] = v.value

    if len(c.bars_raw) > 30 and c.freq in [Freq.W, Freq.M]:
        if kdj_gold_cross(c.bars_raw, just=False):
            v = Signal(k1=str(freq.value), k2="KDJ状态", v1="金叉")
            s[v.key] = v.value

    if len(c.bars_raw) > 100:
        close = np.array([x.close for x in c.bars_raw[-100:]])
        ma5 = SMA(close, timeperiod=5)
        if c.bars_raw[-1].close >= ma5[-1]:
            v = Signal(k1=str(freq.value), k2="MA5状态", v1="收盘价在MA5上方", v2='')
            s[v.key] = v.value
            if ma5[-1] > ma5[-2] > ma5[-3]:
                v = Signal(k1=str(freq.value), k2="MA5状态", v1='收盘价在MA5上方', v2="向上趋势")
                s[v.key] = v.value

        diff, dea, macd = MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        if diff[-3:-1].mean() > 0 and dea[-3:-1].mean() > 0 and macd[-3] < macd[-2] < macd[-1]:
            v = Signal(k1=str(freq.value), k2="MACD状态", v1="DIFF大于0", v2='DEA大于0', v3='柱子增大')
            s[v.key] = v.value

    # 倒0笔潜在三买
    if len(c.bi_list) >= 5:
        if c.bi_list[-1].direction == Direction.Down:
            gg = max(c.bi_list[-1].high, c.bi_list[-3].high)
            zg = min(c.bi_list[-1].high, c.bi_list[-3].high)
            zd = max(c.bi_list[-1].low, c.bi_list[-3].low)
        else:
            gg = max(c.bi_list[-2].high, c.bi_list[-4].high)
            zg = min(c.bi_list[-2].high, c.bi_list[-4].high)
            zd = max(c.bi_list[-2].low, c.bi_list[-4].low)

        if zg > zd:
            k1 = str(freq.value)
            k2 = "倒0笔"
            k3 = "潜在三买"
            v = Signal(k1=k1, k2=k2, k3=k3, v1="构成中枢")
            if gg * 1.1 > min([x.low for x in c.bars_raw[-3:]]) > zg > zd:
                v = Signal(k1=k1, k2=k2, k3=k3,  v1="构成中枢", v2="近3K在中枢上沿附近")
                if max([x.high for x in c.bars_raw[-7:-3]]) > gg:
                    v = Signal(k1=k1, k2=k2, k3=k3, v1="构成中枢", v2="近3K在中枢上沿附近", v3='近7K突破中枢GG')

            if v and "其他" not in v.value:
                s[v.key] = v.value

    return s



def get_macd_third_buy(c: CZSC, di=55):
    """
    N日总成交额信号
    c：basebar
    di:基础K线数量

    完全分类：

    Signal('日线_70根K线MACD_与0轴交叉次数_3次以下_任意_任意_0'),
    Signal('日线_70根K线MACD_与0轴交叉次数_4次以上_任意_任意_0'),

    Signal('日线_70根K线DEA_上穿0轴次数_1次_任意_任意_0'),

    Signal('日线_倒3K_MACD方向_向上_任意_任意_0'),
    Signal('日线_倒3K_MACD方向_模糊_任意_任意_0'),
    Signal('日线_倒3K_MACD方向_向下_任意_任意_0'),

    Signal('日线_金叉面积_背驰_是_任意_任意_0'),

    Signal('日线_K线价格_冲高回落_中枢之上_任意_任意_0')
    Signal('日线_K线价格_冲高回落_中枢之内_任意_任意_0')

    """

    s = OrderedDict()
    freq: Freq = c.freq

    default_signals = [
        Signal(k1=str(freq.value), k2=f"{di}根K线MACD", k3=f"与0轴交叉次数", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(freq.value), k2=f"{di}根K线DEA", k3=f"上穿0轴次数", v1="其他", v2='其他', v3='其他'),

        Signal(k1=str(freq.value), k2='倒3K', k3="MACD方向", v1="其他", v2='其他', v3='其他'),

        Signal(k1=str(freq.value), k2='金叉面积', k3="背驰", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(freq.value), k2='死叉面积', k3="背驰", v1="其他", v2='其他', v3='其他'),

        Signal(k1=str(freq.value), k2='K线价格', k3="冲高回落", v1="其他", v2='其他', v3='其他'),

        Signal(k1=str(freq.value), k2='死叉快线', k3="背驰", v1="其他", v2='其他', v3='其他'),

        Signal(k1=str(freq.value), k2=f"近30根K线DEA", k3="处于0轴以上", v1="其他", v2='其他', v3='其他'),

        Signal(k1=str(freq.value), k2=f"近30根K线DIF", k3="回抽0轴", v1="其他", v2='其他', v3='其他')

    ]

    for signal in default_signals:
        s[signal.key] = signal.value

    if len(c.bars_raw) < di + 40:
        return s

    # 最近几十根根K线的收盘价列表(为了计算准确，多计算40根K线）
    close = np.array([x.close for x in c.bars_raw][-(di + 40):])
    dif, dea, macd = MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

    # 只取最后di根K线的指标
    dif = dif[-di:]
    dea = dea[-di:]

    cross = utils.check_cross_info(dif, dea)
    list = [i for i in cross if i['距离'] >= 2]  # 过滤低级别信号抖动造成的金叉死叉(这个参数根据自身需要进行修改）
    cross_ = []

    for i in range(0, len(list) - 1):
        if len(cross_) >= 1 and list[i]['类型'] == list[i - 1]['类型']:
            # 不将上一个元素加入cross_
            del cross_[-1]
            cross_.append(list[i])
        else:
            cross_.append(list[i])
    num = len(cross_)

    # macd与0轴交叉次数
    if num <= 3:
        v = Signal(k1=str(freq.value), k2=f"{di}根K线MACD", k3=f"与0轴交叉次数", v1="3次以下")
    elif num >= 4:
        v = Signal(k1=str(freq.value), k2=f"{di}根K线MACD", k3=f"与0轴交叉次数", v1="4次以上")
    s[v.key] = v.value

    # dea上穿0轴
    count = utils.down_cross_count([0 for i in range(len(dea))], dea)

    # 上穿一次0轴，最后一根K线的DEA在0轴上，倒数第5根K线DEA在0轴下
    if count == 1 and dea[-1] > 0 and dea[-20] < 0:
        v = Signal(k1=str(freq.value), k2=f"{di}根K线DEA", k3="上穿0轴次数", v1=f"{count}次")
    s[v.key] = v.value

    # 上穿一次或始终处于0轴上方，最近X根K线macd均处于0轴上方
    if count <= 1 and dea[-1] > 0 and dea[-30] > 0:
        v = Signal(k1=str(freq.value), k2=f"近30根K线DEA", k3="处于0轴以上", v1=f"是")
    s[v.key] = v.value

    # 近30根K线的dif的最小值，在正负0.2*dif最大值区间内，即回抽0轴
    if - max(dif[-30:]) * 0.2 < min(dif[-30:]) < max(dif[-30:]) * 0.2:
        v = Signal(k1=str(freq.value), k2=f"近30根K线DIF", k3="回抽0轴", v1=f"是")
    s[v.key] = v.value

    # 最近3根 MACD 方向信号
    if macd[-1] > macd[-2] > macd[-3]:
        v = Signal(k1=str(freq.value), k2='倒3K', k3="MACD方向", v1="向上")
    elif macd[-1] < macd[-2] < macd[-3]:
        v = Signal(k1=str(freq.value), k2='倒3K', k3="MACD方向", v1="向下")
    else:
        v = Signal(k1=str(freq.value), k2='倒3K', k3="MACD方向", v1="模糊")
    s[v.key] = v.value

    # 金叉判断基于剔除抖动的cross_列表
    gold_x = [i for i in cross_ if i['类型'] == '金叉']

    # 死叉判断基于不剔除抖动的cross列表
    die_x = [i for i in cross if i['类型'] == '死叉']

    # 最后一次金叉的面积 < 倒数第二次金叉的面积
    if len(gold_x) >= 2 and gold_x[-1]['面积'] < gold_x[-2]['面积']:
        v = Signal(k1=str(freq.value), k2='金叉面积', k3="背驰", v1="是")
    else:
        v = Signal(k1=str(freq.value), k2='金叉面积', k3="背驰", v1="其他")
    s[v.key] = v.value

    if len(die_x) >= 2 and die_x[-1]['面积'] < die_x[-2]['面积']:
        v = Signal(k1=str(freq.value), k2='死叉面积', k3="背驰", v1="是")
    else:
        v = Signal(k1=str(freq.value), k2='死叉面积', k3="背驰", v1="其他")
    s[v.key] = v.value

    # 死叉快线高点背驰（设置一个参数，让背驰更突出一些，比如小于上一个高点的0.8）
    if len(die_x) >= 2 and 0 < die_x[-1]['快线高点'] < die_x[-2]['快线高点'] * 0.8:
        v = Signal(k1=str(freq.value), k2='死叉快线', k3="背驰", v1="是")
    else:
        v = Signal(k1=str(freq.value), k2='死叉快线', k3="背驰", v1="其他")
    s[v.key] = v.value

    high_zs = max([x.high for x in c.bars_raw][-di:-20])
    high_last_bi = max([x.high for x in c.bars_raw][-20:])
    low_last_bi = min([x.low for x in c.bars_raw][-3:])

    if high_zs < low_last_bi < high_last_bi < high_zs * 1.1:
        v = Signal(k1=str(freq.value), k2='K线价格', k3="冲高回落", v1="中枢之上")
    elif high_zs > low_last_bi:
        v = Signal(k1=str(freq.value), k2='K线价格', k3="冲高回落", v1="中枢之内")
    else:
        v = Signal(k1=str(freq.value), k2='K线价格', k3="冲高回落", v1="其他")
    s[v.key] = v.value

    return s