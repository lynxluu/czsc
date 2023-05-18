from loguru import logger
try:
    import talib as ta
except:
    logger.warning(f"ta-lib 没有正确安装，相关信号函数无法正常执行。"
                   f"请参考安装教程 https://blog.csdn.net/qaz2134560/article/details/98484091")
import numpy as np
from collections import OrderedDict
from czsc import CZSC, Freq, Signal, CzscAdvancedTrader, RawBar, NewBar
from czsc.signals.utils import check_cross_info, down_cross_count



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
    # dif, dea, macd = MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    dif = [x.cache['MACD']['dif'] for x in c.bars_raw[di:]]
    dea = [x.cache['MACD']['dea'] for x in c.bars_raw[di:]]
    macd = [x.cache['MACD']['macd'] for x in c.bars_raw[di:]]

    # 只取最后di根K线的指标
    dif = dif[-di:]
    dea = dea[-di:]

    cross = check_cross_info(dif, dea)
    list = [i for i in cross if i['距离'] >= 2]  # 过滤低级别信号抖动造成的金叉死叉(这个参数根据自身需要进行修改）
    cross_ = []

    for i in range(0, len(list)-1):
        if len(cross_) >= 1 and list[i]['类型'] == list[i-1]['类型']:
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
    count = down_cross_count([0 for i in range(len(dea))], dea)

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












def trader_third_buy_D(symbol, T0=False, min_interval=0):
    """A股市场择时策略样例，支持按交易标的独立设置参数

    :param symbol:
    :param T0: 是否允许T0交易
    :param min_interval: 最小开仓时间间隔，单位：秒
    :return:
    """

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        s.update(signals.pos.get_s_long01(cat, th=500))  # 5个点止损
        s.update(signals.pos.get_s_long02(cat, th=1500))  # 回撤20%止盈

        signals.update_macd_cache(cat.kas['日线'])

        for _, c in cat.kas.items():
            if c.freq == Freq.D:
                s.update(get_macd_third_buy(c))
        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=T0, long_min_interval=min_interval)

    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name="日线三买", signals_all=[
                Signal('日线_55根K线MACD_与0轴交叉次数_4次以上_任意_任意_0'),
                Signal('日线_55根K线DEA_上穿0轴次数_1次_任意_任意_0'),
                Signal('日线_金叉面积_背驰_是_任意_任意_0'),
                Signal('日线_K线价格_冲高回落_中枢之上_任意_任意_0')
            ], signals_any=[
                Signal('日线_倒3K_MACD方向_向下_任意_任意_0'),
                Signal('日线_倒3K_MACD方向_模糊_任意_任意_0'),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE, factors=[
            Factor(name="日线一卖", signals_all=[
                Signal('日线_55根K线MACD_与0轴交叉次数_4次以上_任意_任意_0'),
                Signal('日线_近30根K线DEA_处于0轴以上_是_任意_任意_0'),
                Signal('日线_近30根K线DIF_回抽0轴_是_任意_任意_0'),
            ], signals_any=[
                Signal('日线_死叉面积_背驰_是_任意_任意_0'),
                Signal('日线_死叉快线_背驰_是_任意_任意_0'),
            ]),
            Factor(name="三买破坏", signals_all=[
                Signal('日线_K线价格_冲高回落_中枢之内_任意_任意_0')]),
            Factor(name="止损5%", signals_all=[
                Signal("多头_亏损_超500BP_是_任意_任意_0")]),
            Factor(name="最大回撤15%", signals_all=[
                Signal("多头_回撤_超1500BP_是_任意_任意_0")]),
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