# -*- coding: utf-8 -*-
"""
author: maming
email: 569761648@qq.com
create_dt: 2022/12/07 23:16
describe:
"""
from collections import OrderedDict
from czsc import CZSC, signals
from czsc.data import TsDataCache, get_symbols
from czsc.objects import Freq, Operate, Signal, Factor, Event, PositionLong, PositionShort, RawBar
from czsc.traders import CzscAdvancedTrader
from czsc.utils import get_sub_elements, fast_slow_cross
from czsc.signals.utils import down_cross_count, check_cross_info
from czsc.signals.tas import update_macd_cache


def tas_dea_cross_V221106(c: CZSC, n=55) -> OrderedDict:
    """dea穿过0轴次数

    信号逻辑：
    计算近di根k线的dea与0轴的相对位置

    信号列表：
    - Signal('日线_K55DEA_上穿0轴_1次_任意_任意_0')
    - Signal('日线_K55DEA_处于0轴以上_是_任意_任意_0')
    - Signal('日线_K55DEA_处于0轴以下_是_任意_任意_0')

    :param c: CZSC对象
    :param n: 连续倒3根K线
    :return:
    """

    s = OrderedDict()
    default_signals = [
        Signal(k1=str(c.freq.value), k2=f"K{n}DEA", k3="上穿0轴", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(c.freq.value), k2=f"K{n}DEA", k3="处于0轴以上", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(c.freq.value), k2=f"K{n}DEA", k3="处于0轴以下", v1="其他", v2='其他', v3='其他')
    ]
    for signal in default_signals:
        s[signal.key] = signal.value
    bars = get_sub_elements(c.bars_raw, di=1, n=n)

    if not bars[0].cache:
        return s

    dea = [x.cache['MACD']['dea'] for x in bars]

    # dea上穿0轴
    up = down_cross_count([0 for i in range(len(dea))], dea)
    down = down_cross_count(dea, [0 for i in range(len(dea))])

    # 上穿一次0轴，最后一根K线的DEA在0轴上，倒数第5根K线DEA在0轴下
    if up == 1 and down == 0 and dea[-1] > 0:
        v = Signal(k1=str(c.freq.value), k2=f"K{n}DEA", k3="上穿0轴", v1=f"1次")
        s[v.key] = v.value

    # 上穿一次或始终处于0轴上方，最近X根K线macd均处于0轴上方
    if up == down == 0 and dea[-n] > 0:
        v = Signal(k1=str(c.freq.value), k2=f"K{n}DEA", k3="处于0轴以上", v1=f"是")
        s[v.key] = v.value
    elif up == down == 0 and dea[-n] < 0:
        v = Signal(k1=str(c.freq.value), k2=f"K{n}DEA", k3="处于0轴以下", v1=f"是")
        s[v.key] = v.value

    return s

# macd柱子面积背驰
def tas_macd_area_compare_V221106(c: CZSC, n: int = 55) -> OrderedDict:
    """MACD柱子面积背驰
    信号逻辑：
    计算最近n根K线周期中，两次相邻macd柱子面积背驰比较

    信号列表：
    - Signal('日线_K55绿柱子_背驰_否_任意_任意_0')
    - Signal('日线_K55绿柱子_背驰_是_任意_任意_0')
    - Signal('日线_K55红柱子_背驰_否_任意_任意_0')
    - Signal('日线_K55红柱子_背驰_是_任意_任意_0')

    :param c: czsc对象
    :param n:最近di跟K线
    :return:
    """

    s = OrderedDict()
    k1, k2, k3 = f"{c.freq.value}_K{n}绿柱子_背驰".split('_')
    m1, m2, m3 = f"{c.freq.value}_K{n}红柱子_背驰".split('_')

    bars = get_sub_elements(c.bars_raw, di=1, n=n)
    if not bars[0].cache:
        v = Signal(k1=k1, k2=k2, k3=k3, v1="其他", v2="其他", v3="其他")
        w = Signal(k1=m1, k2=m2, k3=m3, v1="其他", v2="其他", v3="其他")
        s[v.key] = v.value
        s[w.key] = w.value
        return s

    dif = [x.cache['MACD']['dif'] for x in bars]
    dea = [x.cache['MACD']['dea'] for x in bars]

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

    # 最后一次金叉的面积 < 倒数第二次金叉的面积
    if len(gold_x) >= 2 and gold_x[-1]['面积'] < gold_x[-2]['面积']:
        v1 = "是"
    else:
        v1 = '否'
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1)
    s[signal.key] = signal.value

    if len(die_x) >= 2 and die_x[-1]['面积'] < die_x[-2]['面积']:
        w1 = '是'
    else:
        w1 = '否'
    signal = Signal(k1=m1, k2=m2, k3=m3, v1=w1)
    s[signal.key] = signal.value

    return s

def tas_dif_zero_V221106(c: CZSC, n=55) -> OrderedDict:
    """dif回抽0轴

    信号逻辑：
    1.首先在基于di根k线为一段向上趋势；
    2.其次确定di期间dif处于下降趋势；
    3.在以上基础上，连续di根k线形成的dif最低点在 +—dif最大值0.2倍之间，在此期间判断为上涨过程中回抽0轴

    信号列表：
    - Signal('日线_K30DIF_回抽0轴_否_任意_任意_0')
    - Signal('日线_K30DIF_回抽0轴_是_任意_任意_0')

    :param c: CZSC对象
    :param n: 连续倒di根K线
    :return:
    """
    s = OrderedDict()
    bars = get_sub_elements(c.bars_raw, di=1, n=n)
    if not bars[0].cache:
        v = Signal(k1=str(c.freq.value), k2=f"K{n}DIF", k3="回抽0轴", v1="其他", v2="其他", v3="其他")
        s[v.key] = v.value
        return s
    dif = [x.cache['MACD']['dif'] for x in bars]

    # 近di根K线的dif的最小值，在正负0.2*dif最大值区间内，即回抽0轴
    if - max(dif) * 0.2 < min(dif) < max(dif) * 0.2:
        v = Signal(k1=str(c.freq.value), k2=f"K{n}DIF", k3="回抽0轴", v1=f"是")
    else:
        v = Signal(k1=str(c.freq.value), k2=f"K{n}DIF", k3="回抽0轴", v1=f"否")
    s[v.key] = v.value
    return s

def macd_zs_v221106(c: CZSC, n=55) -> OrderedDict:
    """dif回抽0轴

    信号逻辑：
    1.划定[-di:-13]区间为中枢区间，取其高点；
    2.取倒13根K线的最高点，此笔为中枢突破；
    3.取倒3笔的低点，判断该点位与中枢的相对位置

    信号列表：
    - Signal('日线_K55价格_冲高回落_中枢之内_任意_任意_0')
    - Signal('日线_K55价格_冲高回落_中枢之上_任意_任意_0')

    :param c: CZSC对象
    :param n: 连续倒di根K线
    :return:
    """
    s = OrderedDict()

    high_zs = max([x.high for x in c.bars_raw][-n:-13])
    high_last_bi = max([x.high for x in c.bars_raw][-13:])
    low_last_bi = min([x.low for x in c.bars_raw][-3:])

    if high_zs < low_last_bi < high_last_bi < high_zs * 1.1:
        v = Signal(k1=str(c.freq.value), k2=f'K{n}价格', k3="冲高回落", v1="中枢之上")
        s[v.key] = v.value
    elif high_zs > low_last_bi:
        v = Signal(k1=str(c.freq.value), k2=f'K{n}价格', k3="冲高回落", v1="中枢之内")
        s[v.key] = v.value
    else:
        v = Signal(k1=str(c.freq.value), k2=f'K{n}价格', k3="冲高回落", v1="其他")
        s[v.key] = v.value

    return s

# macd快线背驰
def tas_macd_quickline_compare_V221106(c: CZSC, n: int = 55) -> OrderedDict:
    """MACD柱子面积背驰
    信号逻辑：
    计算最近di根K线周期中，两次相邻两次金叉或死叉快线高低点背驰比较

    信号列表：
    - Signal('日线_死叉快线_背驰_否_任意_任意_0')
    - Signal('日线_死叉快线_背驰_是_任意_任意_0')
    - Signal('日线_金叉快线_背驰_否_任意_任意_0')
    - Signal('日线_金叉快线_背驰_是_任意_任意_0')

    :param c: czsc对象
    :param n:最近di跟K线
    :return:
    """

    s = OrderedDict()
    k1, k2, k3 = f"{c.freq.value}_死叉快线_背驰".split('_')
    m1, m2, m3 = f"{c.freq.value}_金叉快线_背驰".split('_')

    bars = get_sub_elements(c.bars_raw, di=1, n=n)
    if not bars[0].cache:
        v = Signal(k1=k1, k2=k2, k3=k3, v1="其他", v2="其他", v3="其他")
        w = Signal(k1=m1, k2=m2, k3=m3, v1="其他", v2="其他", v3="其他")
        s[v.key] = v.value
        s[w.key] = w.value
        return s

    dif = [x.cache['MACD']['dif'] for x in bars]
    dea = [x.cache['MACD']['dea'] for x in bars]

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

    # 死叉快线高点背驰（设置一个参数，让背驰更突出一些，比如小于上一个高点的0.8）
    if len(die_x) >= 2 and 0 < die_x[-1]['快线高点'] < die_x[-2]['快线高点'] * 0.8:
        v1 = "是"
    else:
        v1 = '否'
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1)
    s[signal.key] = signal.value

    # 金叉快线高点背驰（设置一个参数，让背驰更突出一些，比如小于上一个高点的0.8）
    if len(gold_x) >= 2 and 0 > gold_x[-1]['快线低点'] > gold_x[-2]['快线低点'] * 0.8:
        w1 = "是"
    else:
        w1 = '否'
    signal = Signal(k1=m1, k2=m2, k3=m3, v1=w1)
    s[signal.key] = signal.value

    return s

def tas_macd_direct_V221106(c: CZSC, di: int = 1) -> OrderedDict:
    """MACD方向；贡献者：马鸣

    **信号逻辑：** 连续三根macd柱子值依次增大，向上；反之，向下

    **信号列表：**

    - Signal('日线_D1K_MACD方向_模糊_任意_任意_0')
    - Signal('日线_D1K_MACD方向_向下_任意_任意_0')
    - Signal('日线_D1K_MACD方向_向上_任意_任意_0')

    :param c: CZSC对象
    :param di: 连续倒3根K线
    :return:
    """
    k1, k2, k3 = f"{c.freq.value}_D{di}K_MACD方向".split("_")
    s = OrderedDict()
    bars = get_sub_elements(c.bars_raw, di=di, n=3)

    if not bars[0].cache:
        v = Signal(k1=k1, k2=k2, k3=k3, v1="其他", v2="其他", v3="其他")
        s[v.key] = v.value
        return s

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
    s = OrderedDict()
    bars = get_sub_elements(c.bars_raw, di=di, n=n)

    if not bars[0].cache:
        v = Signal(k1=k1, k2=k2, k3=k3, v1="其他", v2="其他", v3="其他")
        s[v.key] = v.value
        return s

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

    v = Signal(k1=k1, k2=k2, k3=k3, v1=f"{num}次")
    s[v.key] = v.value
    return s

# 定义择时交易策略，策略函数名称必须是 trader_strategy
# ----------------------------------------------------------------------------------------------------------------------
def trader_strategy(symbol, T0=False, min_interval=0):
    """A股市场择时策略样例，支持按交易标的独立设置参数

    :param symbol:
    :param T0: 是否允许T0交易
    :param min_interval: 最小开仓时间间隔，单位：秒
    :return:
    """

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        # s.update(signals.pos.get_s_long01(cat, th=500))  # 5个点止损
        # s.update(signals.pos.get_s_long02(cat, th=1500))  # 回撤20%止盈
        s.update(signals.bar_operate_span_V221111(cat.kas['15分钟'], k1='交易', span=('0935', '1450')))
        s.update(signals.bar_zdt_V221110(cat.kas['15分钟'], di=1))

        update_macd_cache(cat.kas['日线'])

        s.update(tas_macd_change_V221105(cat.kas['日线'], di=1, n=55))
        s.update(tas_macd_direct_V221106(cat.kas['日线'], di=1))

        s.update(tas_dea_cross_V221106(cat.kas['日线'], n=55))
        s.update(tas_dea_cross_V221106(cat.kas['日线'], n=30))

        s.update(tas_macd_area_compare_V221106(cat.kas['日线'], n=55))
        s.update(macd_zs_v221106(cat.kas['日线'], n=55))
        s.update(tas_dif_zero_V221106(cat.kas['日线'], n=30))
        s.update(tas_macd_quickline_compare_V221106(cat.kas['日线'], n=55))

        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=T0, long_min_interval=min_interval)

    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name="日线三买", signals_all=[
                Signal("交易_0935_1450_是_任意_任意_0"),
                Signal('日线_K55DEA_上穿0轴_1次_任意_任意_0'),
                Signal('日线_K55绿柱子_背驰_是_任意_任意_0'),
                Signal('日线_K55价格_冲高回落_中枢之上_任意_任意_0'),
                Signal('日线_D1K55_MACD变色次数_3次_任意_任意_0'),
            ],
            #        signals_any=[
            #     Signal('日线_D1K55_MACD变色次数_3次_任意_任意_0'),
            #     Signal('日线_D1K55_MACD变色次数_4次_任意_任意_0'),
            #     Signal('日线_D1K55_MACD变色次数_5次_任意_任意_0'),
            #     Signal('日线_D1K55_MACD变色次数_6次_任意_任意_0'),
            # ],
                   signals_not=[
                Signal("15分钟_D1K_ZDT_涨停_任意_任意_0"),
                Signal('日线_D1K_MACD方向_向上_任意_任意_0'),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE,
              signals_all=[
                  Signal("交易_0935_1450_是_任意_任意_0"),
                  Signal("15分钟_D1K_ZDT_其他_任意_任意_0"),
              ], factors=[
                Factor(name="日线一卖", signals_all=[
                    Signal('日线_K30DEA_处于0轴以上_是_任意_任意_0'),
                    Signal('日线_K30DIF_回抽0轴_是_任意_任意_0'),
                ], signals_any=[
                    Signal('日线_K55红柱子_背驰_是_任意_任意_0'),
                    Signal('日线_死叉快线_背驰_是_任意_任意_0'),
                ]),
                Factor(name="三买破坏", signals_all=[
                    Signal('日线_K55价格_冲高回落_中枢之内_任意_任意_0')]),
                # Factor(name="止损5%", signals_all=[
                #     Signal("多头_亏损_超500BP_是_任意_任意_0")]),
                # Factor(name="最大回撤15%", signals_all=[
                #     Signal("多头_回撤_超1500BP_是_任意_任意_0")]),
            ]),

    ]

    tactic = {
        "base_freq": '15分钟',
        "freqs": ['日线'],
        "get_signals": get_signals,
        "signals_n": 0,

        "long_pos": long_pos,
        "long_events": long_events,

        # 空头策略不进行定义，也就是不做空头交易
        "short_pos": None,
        "short_events": None,
    }

    return tactic


# 定义命令行接口的特定参数
# ----------------------------------------------------------------------------------------------------------------------

# 初始化 Tushare 数据缓存
dc = TsDataCache(r"d:\ts_data")

# 定义回测使用的标的列表
symbols = get_symbols(dc, 'train20')

# 【必须】策略回测参数设置
dummy_params = {
    "symbols": symbols,  # 回测使用的标的列表
    "sdt": "20150101",  # K线数据开始时间
    "mdt": "20200101",  # 策略回测开始时间
    "edt": "20221231",  # 策略回测结束时间
}

# 执行结果路径
results_path = r"d:\ts_data\macd_3bs_mm"

# 策略回放参数设置【可选】
replay_params = {
    "symbol": "000001.SZ#E",  # 回放交易品种
    "sdt": "20150101",  # K线数据开始时间
    "mdt": "20180101",  # 策略回放开始时间
    "edt": "20220101",  # 策略回放结束时间
}
